import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


def create_addon_package(output_path=None, output_dir=None):
    """Create an Anki addon package

    Args:
        output_path: Path to output .ankiaddon file
        output_dir: Path to output directory for direct addon installation
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # 1. Copy addon_package contents to temp directory
        addon_dir = temp_dir / 'addon'
        shutil.copytree('addon_package', addon_dir, dirs_exist_ok=True)

        # 2. Copy anki_deck_generator into addon_package
        shutil.copytree(
            'anki_deck_generator',
            addon_dir / 'anki_deck_generator',
            ignore=lambda src, _: {'__init__.py'} if src == 'anki_deck_generator' else set(),
            dirs_exist_ok=True
        )

        # 3. Install dependencies
        deps_dir = addon_dir / 'dependencies'
        deps_dir.mkdir(exist_ok=True)
        subprocess.check_call([
            'pip', 'install',
            # '--platform', 'win_amd64',  # TODO: fix bin packages for different platforms
            # '--python-version', '3.9',
            '-r', str(addon_dir / 'requirements.txt'),
            '--target', str(deps_dir)
        ])

        if output_dir:
            output_dir = Path(output_dir)
            if output_dir.exists():
                shutil.rmtree(output_dir)
            shutil.copytree(addon_dir, output_dir, dirs_exist_ok=True)
            return

        # 4. Create zip file
        output_path = Path(output_path)
        if output_path.exists():
            output_path.unlink()

        # Create the zip file from the addon directory
        shutil.make_archive(str(output_path.with_suffix('')), 'zip', addon_dir)

        # Rename .zip to .ankiaddon if needed
        if output_path.suffix == '.ankiaddon':
            zip_path = output_path.with_suffix('.zip')
            zip_path.rename(output_path)


def main():
    parser = argparse.ArgumentParser(description='Build Anki addon package')

    # Create mutually exclusive group for output options
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        '-o', '--output',
        default='anki_deck_generator.ankiaddon',
        help='Output path for the addon package'
    )
    output_group.add_argument(
        '-d', '--output-dir',
        help='Output directory for direct addon installation'
    )

    args = parser.parse_args()

    create_addon_package(
        output_path=args.output if not args.output_dir else None,
        output_dir=args.output_dir
    )

    if args.output_dir:
        print(f'Addon files created in directory: {args.output_dir}')
    else:
        print(f'Addon package created at: {args.output}')


if __name__ == '__main__':
    main()
