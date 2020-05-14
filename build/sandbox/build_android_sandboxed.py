# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Builds an Android target in a secure sandbox."""

import argparse
import os
from . import config
from . import nsjail


def build(android_target, variant, nsjail_bin, chroot, dist_dir, build_id,
          max_cpus, build_goals, overlay_config=None,
          readonly_bind_mount=None):
  """Builds an Android target in a secure sandbox.

  Args:
    android_target: A string with the name of the android target to build.
    variant: A string with the build variant.
    nsjail_bin: A string with the path to the nsjail binary.
    chroot: A string with the path to the chroot of the NsJail sandbox.
    dist_dir: A string with the path to the Android dist directory.
    build_id: A string with the Android build identifier.
    max_cpus: An integer with maximum number of CPUs.
    build_goals: A list of strings with the goals and options to provide to the
      build command.
    overlay_config: A string path to an overlay configuration file.
    readonly_bind_mount: A string path to a path to be mounted as read-only.

  Returns:
    A list of commands that were executed. Each command is a list of strings.
  """
  # All builds are required to run with the root of the
  # Android source tree as the current directory.
  source_dir = os.getcwd()
  command = [
      '/src/tools/treble/build/sandbox/build_android_target.sh',
      '%s-%s' % (android_target, variant),
      '/src',
      'make',
      '-j',
  ] + build_goals

  readonly_bind_mounts = []
  if readonly_bind_mount:
    readonly_bind_mounts = [readonly_bind_mount]

  return nsjail.run(
      nsjail_bin=nsjail_bin,
      chroot=chroot,
      overlay_config=overlay_config,
      source_dir=source_dir,
      command=command,
      android_target=android_target,
      dist_dir=dist_dir,
      build_id=build_id,
      max_cpus=max_cpus,
      readonly_bind_mounts=readonly_bind_mounts)


def arg_parser():
  """Returns an ArgumentParser for sanboxed android builds."""
  # Use the top level module docstring for the help description
  parser = argparse.ArgumentParser(
      description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument(
      '--build_target',
      help='The build target.')
  parser.add_argument(
      '--variant', default='userdebug', help='The Android build variant.')
  parser.add_argument(
      '--nsjail_bin',
      required=True,
      help='Path to NsJail binary.')
  parser.add_argument(
      '--chroot',
      required=True,
      help='Path to the chroot to be used for building the Android '
      'platform. This will be mounted as the root filesystem in the '
      'NsJail sandbox.')
  parser.add_argument(
      '--overlay_config',
      required=True,
      help='Path to the overlay configuration file.')
  parser.add_argument(
      '--readonly_bind_mount',
      help='Path to the a path to be mounted as readonly inside the secure '
      'build sandbox.')
  parser.add_argument(
      '--dist_dir',
      help='Path to the Android dist directory. This is where '
      'Android platform release artifacts will be written.')
  parser.add_argument(
      '--build_id',
      help='Build identifier what will label the Android platform '
      'release artifacts.')
  parser.add_argument(
      '--max_cpus',
      type=int,
      help='Limit of concurrent CPU cores that the NsJail sanbox '
      'can use.')
  return parser


def parse_args(parser):
  """Parses command line arguments.

  Returns:
    A dict of all the arguments parsed.
  """
  # Convert the Namespace object to a dict
  return vars(parser.parse_args())


def build_target(android_target,
                 variant,
                 build_goals=['droid', 'dist', 'platform_tests']):
  """Build the specified Android target using the standard build goals

  Args:
    android_target: A string with the name of the android target to build.
    variant: A string with the build variant.
    build_goals: A list of strings with the goals and options to provide to the
      build command.

  Returns:
    None
  """
  args = parse_args(arg_parser())
  build(android_target, variant, build_goals=build_goals, **args)


def main():
  args = parse_args(arg_parser())
  print(args)

  # The --build_target argument could not be required
  # using the standard 'required' argparse option because
  # the argparser is reused by merge_android_sandboxed.py which
  # does not require --build_target.
  if args['build_target'] is None:
    raise ValueError('--build_target is required.')

  cfg = config.Config(args['overlay_config'])
  android_target = cfg.get_build_config_android_target(args['build_target'])
  build_goals = cfg.get_build_config_build_goals(args['build_target'])

  build(
      android_target=android_target,
      variant=args['variant'],
      nsjail_bin=args['nsjail_bin'],
      chroot=args['chroot'],
      overlay_config=args['overlay_config'],
      readonly_bind_mount=args['readonly_bind_mount'],
      dist_dir=args['dist_dir'],
      build_id=args['build_id'],
      max_cpus=args['max_cpus'],
      build_goals=build_goals)


if __name__ == '__main__':
  main()