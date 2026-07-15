import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const rootDir = dirname(dirname(fileURLToPath(import.meta.url)));
const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const venvPython = process.platform === 'win32'
  ? join(rootDir, '.venv', 'Scripts', 'python.exe')
  : join(rootDir, '.venv', 'bin', 'python');

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: rootDir,
    stdio: 'inherit',
    shell: false,
    ...options,
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function findPython() {
  const candidates = [
    process.env.PYTHON,
    process.platform === 'win32' ? 'py' : null,
    'python3',
    'python',
  ].filter(Boolean);

  for (const command of candidates) {
    const args = command === 'py' ? ['-3', '--version'] : ['--version'];
    const result = spawnSync(command, args, { stdio: 'ignore', shell: false });
    if (result.status === 0) {
      return command;
    }
  }

  console.error('Could not find Python. Install Python 3.11+ and try again.');
  process.exit(1);
}

const python = findPython();
const venvArgs = python === 'py'
  ? ['-3', '-m', 'venv', '.venv']
  : ['-m', 'venv', '.venv'];

if (!existsSync(venvPython)) {
  run(python, venvArgs);
}

run(venvPython, ['-m', 'pip', 'install', '--upgrade', 'pip']);
run(venvPython, ['-m', 'pip', 'install', '-r', 'requirements.txt']);
run(npmCommand, ['--prefix', 'frontend', 'install']);
