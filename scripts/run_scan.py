from glob import glob
import os
import json
import yaml
import argparse
import subprocess

def get_args():
    parser = argparse.ArgumentParser(description="Run combine workflow for CP analysis")
    parser.add_argument('-c', '--config', default='configs/harvestDatacards.yml',
                        help='harvestDatacards YAML config')
    return parser.parse_args()

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
        print("\n")
        print("*"*140)
        print(f"\033[1;32m\nCommand '{command}' ran successfully!\n\033[0m")
        print("*"*140)
        print("\n")
    except subprocess.CalledProcessError as e:
        print("\n")
        print("*"*140)
        print(f"\033[1;31m\nCommand '{command}' failed with exit code: {e.returncode}\n\033[0m")
        print("*"*140)
        print("\n")
        raise

def _parameter_string(params):
    return ','.join(f'{k}={v}' for k, v in params.items())


def run_scan(cfg):
    with open(cfg, 'r') as file:
       setup = yaml.safe_load(file)

    folder = setup['output_folder']
    t2w_options = ' '.join(f'--PO {opt}' for opt in setup.get('t2w_physics_options', []))
    scan = setup.get('alpha_scan', {})
    alpha_range = scan.get('range', [-90, 90])
    points = scan.get('points', 21)
    params = scan.get('set_parameters', {'muV': 1, 'alpha': 0, 'muggH': 1, 'mutautau': 1})
    name = scan.get('name', '.alpha')
    plot = scan.get('plot', {})
    plot_x_min = plot.get('x_min', alpha_range[0])
    plot_x_max = plot.get('x_max', alpha_range[1])
    plot_y_max = plot.get('y_max', 8)
    plot_ch_label = plot.get('channel_label')
    plot_label_arg = f" --ch-label='{plot_ch_label}'" if plot_ch_label else ""

    # HARVEST DATACARDS
    run_command(f"python3 scripts/harvestDatacards.py -c {cfg}")
    # CREATE COMBINE WORKSPACE
    run_command(f"combineTool.py -m 125 -M T2W -P CombineHarvester.Combine_HtautauCP.CPMixtureDecays:CPMixtureDecays {t2w_options} -i {folder}/cmb -o ws.root --parallel 8")
    # RUN MAX LIKELIHOOD FIT
    run_command(f"combineTool.py -m 125 -M MultiDimFit --setParameters {_parameter_string(params)} --setParameterRanges alpha={alpha_range[0]},{alpha_range[1]} --points {points} --redefineSignalPOIs alpha  -d {folder}/cmb/ws.root --algo grid -t -1 --there -n {name} --alignEdges 1")
    # PLOT 1D SCAN OF ALPHA
    run_command(f"python3 scripts/plot1DScan.py --main={folder}/cmb/higgsCombine{name}.MultiDimFit.mH125.root --POI=alpha --output={folder}/alpha_cmb --no-numbers --no-box --x-min={plot_x_min} --x-max={plot_x_max} --y-max={plot_y_max}{plot_label_arg}")


def main():
    args = get_args()
    try:
        run_scan(args.config)
    except subprocess.CalledProcessError:
        raise RuntimeError("Production failed!")

if __name__ == "__main__":
    main()
