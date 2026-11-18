#!/usr/bin/env python3
"""Offline, conservative article QA against Repomix markdown or a local repository.

No code execution, no network calls, no automatic edits. Findings are evidence-based;
uncertain identifiers are warnings, not claims of errors.
"""
import argparse
import ast
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
from security_scan import scan, PATTERNS

MAX_ARTICLE = 2_000_000
MAX_SOURCE = 8_000_000
EXTENSIONS = {'.py','.js','.jsx','.ts','.tsx','.go','.rs','.java','.tf','.yaml','.yml','.json','.md','.sh','.sql','.toml','.html','.css','.txt','.ini','.cfg'}
PATH_TOKEN = re.compile(r'(?<![\w./-])(?:[\w.-]+/)*[\w.-]+\.(?:py|js|jsx|ts|tsx|go|rs|java|tf|ya?ml|json|md|sh|sql|toml|html|css|txt|ini|cfg)(?![\w./-])',re.I)
LINK = re.compile(r'(?<!!)\[[^\]\n]+\]\((<?[^\s)]+>?)(?:\s+"[^"]*")?\)')
GITHUB_BLOB = re.compile(r'^/([^/]+)/([^/]+)/(?:blob|raw)/(.+)$')
IDENT = re.compile(r'\b([A-Za-z_]\w*)\s*\(')
CODE_SPAN = re.compile(r'(?<!`)`([^`\n]+)`(?!`)')
EXCLUDED = {'print','len','range','int','str','list','dict','set','tuple','bool','open','super','type','isinstance','any','all','sum','min','max','sorted','enumerate','zip','get','append','read','write','json','main','python','bash'}

def markdown_destinations(line):
    """Yield link destinations with balanced parentheses; ignore image links.

    This is a conservative single-line Markdown parser, not a full CommonMark parser.
    """
    for match in re.finditer(r'(?<!!)\[[^\]\n]+\]\(', line):
        # An escaped opening bracket is literal Markdown, not a link.
        opening=match.start()
        escapes=0
        while opening-escapes-1>=0 and line[opening-escapes-1]=='\\':
            escapes+=1
        if escapes%2:
            continue
        pos=match.end(); start=pos; depth=1; angle=False
        if pos < len(line) and line[pos] == '<':
            angle=True; pos+=1; start=pos
            end=line.find('>',pos)
            if end<0: continue
            url=line[start:end]; pos=end+1
            if pos<len(line) and line[pos]==')': yield url
            elif re.fullmatch(r'\s+"[^"\n]*"\)',line[pos:]): yield url
            continue
        while pos<len(line):
            c=line[pos]
            if c=='\\':
                pos+=2; continue
            if c=='(':
                depth+=1
            elif c==')':
                depth-=1
                if depth==0:
                    yield line[start:pos]; break
            elif c.isspace() and depth==1:
                # Optional Markdown title after destination.
                tail=line[pos:]
                if re.match(r'^\s+"[^"\n]*"\)',tail):
                    yield line[start:pos]
                break
            pos+=1

def mask_inline_code(line):
    """Mask CommonMark-style matching backtick runs, preserving offsets."""
    runs=list(re.finditer(r'`+', line))
    chars=list(line)
    i=0
    while i<len(runs):
        opener=runs[i]
        j=i+1
        while j<len(runs) and len(runs[j].group())!=len(opener.group()):
            j+=1
        if j==len(runs):
            i+=1
            continue
        for k in range(opener.start(),runs[j].end()):
            chars[k]=' '
        i=j+1
    return ''.join(chars)

def inline_code_values(line):
    """Extract matched Markdown code spans with equal-length backtick delimiters."""
    runs = list(re.finditer(r'`+', line))
    i = 0
    while i < len(runs):
        opener = runs[i]
        j = i + 1
        while j < len(runs) and len(runs[j].group()) != len(opener.group()):
            j += 1
        if j == len(runs):
            i += 1
            continue
        value = line[opener.end():runs[j].start()].replace('\n', ' ')
        if value.startswith(' ') and value.endswith(' ') and value.strip(' '):
            value = value[1:-1]
        yield value
        i = j + 1


def reference_label(value):
    """CommonMark-style whitespace/case normalization for reference IDs."""
    return ' '.join(value.split()).casefold()

def reference_definitions(lines, code_lines):
    """Collect single-line reference destinations; first definition wins."""
    result={}
    for number,line in enumerate(lines,1):
        if number in code_lines: continue
        line=mask_inline_code(line)
        m=re.match(r'^ {0,3}\[([^]\n]+)\]:\s*(<[^>\n]+>|\S+)',line)
        if m and not m.group(1).startswith('\\'):
            key=reference_label(m.group(1))
            if key and key not in result:
                raw=m.group(2)
                result[key]=(raw[1:-1] if raw.startswith('<') and raw.endswith('>') else raw,number)
    return result

def reference_uses(line):
    """Explicit [text][id] and collapsed [text][] links, excluding images."""
    for m in re.finditer(r'(?<!!)\[([^]\n]+)\]\[([^]\n]*)\]',line):
        escapes=0
        while m.start()-escapes-1>=0 and line[m.start()-escapes-1]=='\\':
            escapes+=1
        if escapes%2: continue
        yield reference_label(m.group(2) or m.group(1))

def safe_path(value):
    value=value.replace('\\','/')
    if value.startswith('/') or re.match(r'^[a-zA-Z]:',value) or '\x00' in value: return None
    parts=PurePosixPath(value).parts
    if not parts or any(p in ('.','..') for p in parts): return None
    return '/'.join(parts)

def from_repomix(content):
    if len(content.encode('utf-8'))>MAX_SOURCE: raise ValueError('Repomix source too large')
    files={}
    # Parse file entries sequentially: a "## File:" string inside source code
    # is not another entry, and closing fences must match the opener.
    lines=content.splitlines(keepends=True)
    i=0
    while i<len(lines):
        header=re.fullmatch(r'## File: (.+?)\s*',lines[i].rstrip('\r\n'))
        if not header or i+1>=len(lines):
            i+=1;continue
        opener=re.fullmatch(r'(`{3,}|~{3,})[^\r\n]*',lines[i+1].rstrip('\r\n'))
        if not opener:
            i+=1;continue
        marker=opener.group(1)
        j=i+2
        while j<len(lines):
            closing=lines[j].rstrip('\r\n')
            if re.fullmatch(re.escape(marker[0])+r'{'+str(len(marker))+r',}\s*',closing):
                break
            j+=1
        if j==len(lines):
            # Do not silently accept a truncated or malformed source entry.
            raise ValueError('Unclosed Repomix file block: '+header.group(1))
        name=safe_path(header.group(1).strip())
        if name:files[name]=''.join(lines[i+2:j]).rstrip('\r\n')
        i=j+1
    if not files:raise ValueError('No Repomix file entries found')
    return files

def from_directory(root):
    root=Path(root).resolve()
    if not root.is_dir(): raise ValueError('Source directory not found')
    files={}
    total_bytes=0
    for path in root.rglob('*'):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTENSIONS: continue
        rel=path.relative_to(root)
        if any(x in ('.git','node_modules','.venv','venv','dist','build','__pycache__') or x.startswith('.') for x in rel.parts): continue
        # Resolve each candidate: a symlinked ancestor must never escape root.
        if not path.resolve().is_relative_to(root): continue
        size=path.stat().st_size
        if size>200_000: continue
        if total_bytes+size>MAX_SOURCE: raise ValueError('Source directory exceeds total size limit')
        if len(files)>=500: raise ValueError('Too many source files (limit 500)')
        files[rel.as_posix()]=path.read_text(encoding='utf-8',errors='replace')
        total_bytes+=size
    if not files: raise ValueError('No eligible source files found')
    return files

def python_symbols(files):
    symbols={}; parse_fail=[]
    for path,source in files.items():
        if not path.endswith('.py'):continue
        try: tree=ast.parse(source)
        except SyntaxError: parse_fail.append(path);continue
        # Only module-level definitions and class methods are addressable as
        # module.py:name() or module.py:Class.method(). Nested functions are not.
        names=set()
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                names.add(node.name)
                if isinstance(node,ast.ClassDef):
                    for member in node.body:
                        if isinstance(member,(ast.FunctionDef,ast.AsyncFunctionDef)):
                            names.add(node.name+'.'+member.name)
        symbols[path]=names
    return symbols,parse_fail

def redact_secrets(value):
    """Keep matched credentials out of both JSON and Markdown findings."""
    if value is None:
        return None
    value = str(value)
    for pattern in PATTERNS.values():
        value = pattern.sub('[REDACTED_SECRET]', value)
    return value

def validate(article,files,repo=None):
    if len(article.encode('utf-8'))>MAX_ARTICLE:raise ValueError('Article too large')
    findings=[]; lines=article.splitlines(); symbols,parse_fail=python_symbols(files)
    def add(rule,severity,line,message,evidence=None,suggestion=None):
        findings.append({'rule':rule,'severity':severity,'line':line,'message':redact_secrets(message),'evidence':redact_secrets(evidence),'suggestion':redact_secrets(suggestion)})
    fences=[]; code_lines=set(); in_fence=False; start=0; fencechar=''; fence_len=0
    for i,line in enumerate(lines,1):
        m=re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$',line)
        if m:
            seq=m.group(1)
            if not in_fence: in_fence=True;start=i;fencechar=seq[0];fence_len=len(seq)
            elif seq[0]==fencechar and len(seq)>=fence_len and not m.group(2).strip():in_fence=False
            code_lines.add(i);continue
        if in_fence:code_lines.add(i)
    if in_fence:add('MD001','error',start,'Unclosed fenced code block',suggestion='Close the code fence with the same marker')

    # Conservative duplicate prose detection.
    paragraphs=[]; current=[]
    def finish_paragraph():
        if current:
            content=' '.join(piece.strip() for _,piece in current)
            normalized=re.sub(r'\s+', ' ', content).strip()
            if len(normalized)>=100:
                paragraphs.append((current[0][0], normalized))
            current.clear()
    for i,line in enumerate(lines,1):
        stripped=line.strip()
        excluded=(i in code_lines or not stripped or
                  re.match(r'^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||---)',stripped) or
                  stripped.startswith('!['))
        if excluded:
            finish_paragraph()
        else:
            current.append((i,line))
    finish_paragraph()
    for previous,current_para in zip(paragraphs,paragraphs[1:]):
        if previous[1]==current_para[1] and current_para[0]-previous[0]<=12:
            add('TXT001','warning',current_para[0],
                f'Repeated prose paragraph (same text as line {previous[0]})',
                suggestion='Review whether this repetition is intentional')
    headings=[]
    for i,line in enumerate(lines,1):
        if i in code_lines:continue
        h=re.match(r'^\s{0,3}(#{1,6})\s+\S',line)
        if h:
            level=len(h.group(1))
            if headings and level>headings[-1][0]+1:add('MD002','warning',i,'Heading level jumps by more than one',suggestion='Review heading hierarchy')
            headings.append((level,i))
    for label,line in scan(article):add('SEC001','error',line,f'Potential secret detected: {label}',suggestion='Remove or replace with a dummy value; inspect the original locally')
    file_set=set(files)
    definitions=reference_definitions(lines,code_lines)
    def check_link(url,line):
        parsed=urlparse(url)
        if parsed.scheme in ('http','https'):
            if parsed.hostname=='github.com' and repo:
                m=GITHUB_BLOB.match(unquote(parsed.path))
                if m and f'{m.group(1)}/{m.group(2)}'.lower()==repo.lower():
                    tail=m.group(3).split('/')
                    candidates=[safe_path('/'.join(tail[k:])) for k in range(1,len(tail))]
                    if not any(p in file_set for p in candidates if p):
                        if len(tail)==2:
                            path=candidates[0]
                            if path:add('REF002','warning',line,f'GitHub link target not found in supplied source: {path}',suggestion='Check branch and source coverage; verify against GitHub')
                        else:
                            add('REF003','info',line,'GitHub link cannot be verified without resolving the branch/ref',suggestion='Verify the branch and file path on GitHub')
            return
        if parsed.scheme or url.startswith(('#','mailto:')):return
        # Relative links with ../ are dependent on the article's own location,
        # which the CLI does not currently provide; avoid false missing-file claims.
        if unquote(parsed.path).startswith('../'):
            add('LINK002','info',line,'Parent-relative link needs article location to verify',suggestion='Check link relative to the article file')
            return
        path=safe_path(unquote(parsed.path))
        if path and path not in file_set and not (Path(path).suffix.lower() in {'.png','.jpg','.jpeg','.svg','.gif','.webp','.pdf'}):
            add('LINK001','warning',line,f'Local link target not in supplied source: {path}',suggestion='Verify the relative link and source coverage')
    for i,line in enumerate(lines,1):
        if i in code_lines:continue
        # Markdown-looking links inside inline code are examples, not live links.
        # Preserve offsets so other inline-code checks below still see the original line.
        link_line = mask_inline_code(line)
        for url in markdown_destinations(link_line):
            check_link(url,i)
        # Reference definitions are checked when used, not merely declared.
        if not re.match(r'^ {0,3}\[[^]\n]+\]:',link_line):
            for label in reference_uses(link_line):
                if label in definitions:
                    check_link(definitions[label][0],i)
        for span in inline_code_values(line):
            candidate=span.strip()
            if candidate in file_set:continue
            if PATH_TOKEN.fullmatch(candidate) and safe_path(candidate) and candidate not in file_set:
                add('REF001','warning',i,f'File reference not found in supplied source: {candidate}',suggestion='Check spelling or whether the source collection is incomplete')
            # A qualified reference can be checked precisely, but only for
            # parsed Python files. Missing source files must not be treated as
            # evidence that a symbol is absent.
            f=re.fullmatch(r'([\w./-]+\.py):([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)\(\)',candidate)
            if f:
                source_path=safe_path(f.group(1))
                if source_path and source_path not in file_set:
                    add('REF001','warning',i,f'File reference not found in supplied source: {source_path}',suggestion='Check spelling or whether the source collection is incomplete')
                elif source_path in symbols and f.group(2) not in symbols[source_path]:
                    add('PY002','error',i,f'Python symbol absent from {source_path}: {f.group(2)}',evidence=source_path,suggestion='Correct the function name or file reference')
    # Code excerpts are checked only when a heading or prose explicitly identifies a source file.
    for i,line in enumerate(lines,1):
        if i in code_lines:continue
        for m in re.finditer(r'`([A-Za-z_]\w*)\(\)`\s*(?:は|を|が)',line):
            symbol=m.group(1)
            if symbol in EXCLUDED or not symbols:continue
            if any(symbol in s for s in symbols.values()):continue
            add('PY001','warning',i,f'Python-like symbol not found in parsed source: {symbol}()',suggestion='Check whether it is external, built-in, or from an omitted file')
    for path in parse_fail:add('PY003','info',0,f'Python source could not be parsed: {path}',evidence=path)
    counts={s:sum(f['severity']==s for f in findings) for s in ('error','warning','info')}
    return {'schema_version':1,'source_files':len(files),'article_lines':len(lines),'summary':counts,'ok':counts['error']==0,'findings':sorted(findings,key=lambda f:(f['line'],f['rule'])),'limitations':['Offline static checks only; no runtime validation','Warnings can be caused by incomplete source collection','Semantic correctness, secret-free status, and live link reachability are not guaranteed']}

def report_markdown(result):
    s=result['summary'];out=['# Article Kit 品質検査レポート','',f"対象ソース: {result['source_files']}ファイル / 記事: {result['article_lines']}行",f"エラー: {s['error']} / 警告: {s['warning']} / 情報: {s['info']}",'']
    for f in result['findings']:
        out += [f"## {f['severity'].upper()} {f['rule']}（記事{f['line']}行）",f['message']]
        if f['evidence']:out.append('根拠: `'+f['evidence']+'`')
        if f['suggestion']:out.append('対応案: '+f['suggestion'])
        out.append('')
    out += ['## 制限事項','']+['- '+x for x in result['limitations']]
    return '\n'.join(out)+'\n'

def main():
    p = argparse.ArgumentParser(
        description="Article Kit offline article validator v0.41"
    )
    p.add_argument("--article", required=True, type=Path)

    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--context", type=Path, help="Repomix markdown")
    g.add_argument("--source-dir", type=Path, help="Local repository checkout")
    g.add_argument(
        "--article-only",
        action="store_true",
        help="Validate Markdown without repository source files",
    )

    p.add_argument("--repo", help="owner/repo for checking GitHub links")
    p.add_argument(
        "--out", type=Path, default=Path("validation_report")
    )
    args = p.parse_args()

    try:
        article = args.article.read_text(encoding="utf-8-sig")

        if args.article_only:
            from article_only import run
            result = run(article)
        else:
            files = (
                from_repomix(args.context.read_text(encoding="utf-8-sig"))
                if args.context
                else from_directory(args.source_dir)
            )
            result = validate(article, files, args.repo)

        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(
            report_markdown(result), encoding="utf-8"
        )

        print(f"Article Kit QA: {result['summary']}; report: {args.out}")
        return 0 if result["ok"] else 1

    except (OSError, UnicodeError, ValueError) as exc:
        p.exit(2, f"Validation input error: {exc}\n")

if __name__=='__main__':raise SystemExit(main())
