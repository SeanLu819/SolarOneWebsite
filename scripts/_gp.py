import subprocess, os

git_exe = r'C:\Program Files\Git\cmd\git.exe'
cwd = r'e:\Python\PROJECT\website'
res_path = r'e:\Python\PROJECT\website\GR.txt'

lines = []

def run(args):
    cmd = [git_exe, '-C', cwd] + args
    lines.append('\n>>> ' + ' '.join(args))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        if r.stdout: lines.append('  out: ' + r.stdout.strip())
        if r.stderr: lines.append('  err: ' + r.stderr.strip())
        lines.append(f'  [exit={r.returncode}]')
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        lines.append(f'  EXC: {e}')
        return -1, '', ''

os.chdir(cwd)
run(['status', '--short'])
run(['add', '-A'])
# Re-add gitignore entries for temp files (should be in gitignore already)
run(['status', '--short'])

# Commit
rc = subprocess.run([git_exe, '-C', cwd, 'commit', '-m',
                    'fix: 重写WhiteNoise挂载 + vercel.json静态路由 + 静态路径统一规范化 + favicon/logo/pdf/项目图片全修复'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace')
lines.append(f'\n>>> commit\n  out: {rc.stdout.strip()}\n  err: {rc.stderr.strip()}\n  [exit={rc.returncode}]')

# Push
rp = subprocess.run([git_exe, '-C', cwd, 'push', 'origin', 'main'],
                    capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
lines.append(f'\n>>> push\n  out: {rp.stdout.strip()}\n  err: {rp.stderr.strip()}\n  [exit={rp.returncode}]')

with open(res_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('PUSH_DONE')