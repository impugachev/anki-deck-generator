import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def copy_directory(src, dst):
    """Copy directory recursively, creating destination if it doesn't exist"""
    shutil.copytree(src, dst, dirs_exist_ok=True)


def install_dependencies(requirements_file, target_dir):
    """Install pip dependencies to a specific directory"""
    subprocess.check_call([
        'pip', 'install',
        '-r', str(requirements_file),
        '--target', str(target_dir),
        '--no-deps'  # Don't install dependencies of dependencies to keep size minimal
    ])


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
        copy_directory('addon_package', addon_dir)
        
        # 2. Copy anki_deck_generator into addon_package
        copy_directory('anki_deck_generator', addon_dir / 'anki_deck_generator')
        
        # 3. Install dependencies
        deps_dir = addon_dir / 'dependencies'
        deps_dir.mkdir(exist_ok=True)
        install_dependencies(addon_dir / 'requirements.txt', deps_dir)
        
        if output_dir:
            # Copy directly to Anki addons folder
            output_dir = Path(output_dir)
            if output_dir.exists():
                shutil.rmtree(output_dir)
            copy_directory(addon_dir, output_dir)
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