import argparse
import os
import shutil
from pathlib import Path

import logging

def _logpath(path, names):
    logging.info('Working in %s' % path)
    return []   # nothing will be ignored

def copy2_verbose(src, dst):
    print('Copying {0} {1}'.format(src, dst))
    shutil.copy2(src, dst)

def do_build(install_at=None, include_tests=False):
  """Build addon by copying relevant addon directories and files to ./out/blenderkit directory.
  Create zip in ./out/blenderkit.zip.
  """
  shutil.rmtree('out', True)
  target_dir = "out/blender-render-farm"
  ignore_files = [
    '.gitignore',
    'dev.py',
    'README.md',
    # 'CONTRIBUTING.md',
    # 'setup.cfg'
  ]

  os.makedirs(target_dir, exist_ok=True)

  for item in os.listdir():
    if os.path.isdir(item):
      continue # we copied directories above
    if item in ignore_files:
      continue
    if include_tests is False and item == "test.py":
      continue
    if include_tests is False and item.startswith('test_'):
      continue # we do not include test files
    shutil.copy(item, f'{target_dir}/{item}')

  #CREATE ZIP
  shutil.make_archive(target_dir, 'zip', 'out', 'blender-render-farm')

  print(install_at);

  if install_at is not None:
    shutil.rmtree(f'{install_at}/blender-render-farm', ignore_errors=True)
    shutil.copytree(target_dir, f'{install_at}/blender-render-farm', copy_function=copy2_verbose)

### COMMAND LINE INTERFACE

parser = argparse.ArgumentParser()
parser.add_argument(
  "command",
  default='build',
  choices=['build', 'bundle', 'test'],
  help=
  """
  BUILD = copy relevant files into ./out/blenderkit.
  BUNDLE = bundle dependencies into ./dependencies
  TEST = build with test files and run tests
  """
  )
parser.add_argument('--install-at', type=str, default=None, help='If path is specified, then builded addon will be copied to that location.')
args = parser.parse_args()

if args.command == "build":
  do_build(args.install_at)
# elif args.command == "test":
#   do_build(args.install_at, include_tests=True)
#   run_tests()
# elif args.command == "bundle":
#   bundle_dependencies()
else:
  parser.print_help()