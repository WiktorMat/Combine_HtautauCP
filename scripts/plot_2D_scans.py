import warnings
# ignore ROOT/numpy precision related warnings
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r"The value of the smallest subnormal.*"
    )
import matplotlib.pyplot as plt
from matplotlib import ticker
import numpy as np
import ROOT
import seaborn as sns
from scipy import interpolate
from scipy.interpolate import griddata
import matplotlib.colors as mcolors
import mplhep as hep
import argparse
import os


hep.style.use("CMS")
plt.rcParams.update({"font.size": 20})
cmap = sns.color_palette("Blues_r", as_cmap=True)

def get_args():
    parser = argparse.ArgumentParser(description="2D NLL plotter")
    parser.add_argument('--file', type=str, help="file", required=True)
    parser.add_argument('--kappas', action='store_true', help="2D kappa scan")
    parser.add_argument('--mutautau', action='store_true', help="Signal strength vs alpha")
    parser.add_argument('--muvsmu', action='store_true', help="mu ggH vs mu V")

    return parser.parse_args()

def main(args):

    # open root file to get the limi
    f = ROOT.TFile.Open(args.file)
    t = f.Get("limit")

    # Remove bestfit and negative NLL values
    df = ROOT.RDataFrame("limit", args.file)
    df = df.Filter('quantileExpected > -0.5 && deltaNLL > 0 && deltaNLL < 1000').Define("nll", "2*deltaNLL")

    bestfit = ROOT.RDataFrame("limit", args.file).Filter('deltaNLL == 0').AsNumpy()
    # print("Best fit point:", bestfit)

    if args.kappas:

        arrays = df.AsNumpy(["kappaH", "kappaA", "nll"])

        kappaH = arrays["kappaH"]
        kappaA = arrays["kappaA"]
        nll = arrays["nll"]

        # interpolate NLL onto a fine grid
        x_grid = np.linspace(kappaH.min(), kappaH.max(), 3000)
        y_grid = np.linspace(kappaA.min(), kappaA.max(), 3000)
        X, Y = np.meshgrid(x_grid, y_grid)
        NLL_grid = griddata(points=(kappaH, kappaA), values=nll, xi=(X, Y), method='cubic')

        # Get contours (using ROOT for NLL number)
        confidence = [0.683, 0.9545, 0.9973] #, 0.999936657516334, 0.999999426696856]
        levels = [ROOT.Math.chisquared_quantile_c(1 - cl, 2) for cl in confidence]

        print(f"Using NLL thresholds: 1sigma={levels[0]}, 2sigma={levels[1]}, 3sigma={levels[2]}")
        sigma_5 = 28.74370242616088
        # add the equivalent minimum NLL
        bestfit_kappaH = [bestfit['kappaH'][0], -bestfit['kappaH'][0]]
        bestfit_kappaA = [bestfit['kappaA'][0], -bestfit['kappaA'][0]]
        print(f"Best fit at kappaH={bestfit_kappaH}, kappaA={bestfit_kappaA}")


        fig, ax = plt.subplots(figsize=(8,6.5))
        # Add NLL and contours
        im = ax.imshow(NLL_grid, origin='lower', extent=[X.min(), X.max(), Y.min(), Y.max()],cmap=cmap, vmin=0, vmax=sigma_5)
        plt.colorbar(im, label=r"$-2\Delta\ln \mathcal{L}$")
        contours = ax.contour(NLL_grid, levels=levels, colors='black', linestyles=['solid', 'dashdot', 'dashed'], origin='lower', extent=[x_grid.min(), x_grid.max(), y_grid.min(), y_grid.max()])
        # this is hacky but make legends for contours
        contour_handles = []
        for line, CL in zip(['solid', 'dashdot', 'dashed'], confidence):
            h, = ax.plot([], [], color='black', linestyle=line, label=f'{CL:.1%} CL')
            contour_handles.append(h)
        legend_contours = ax.legend(handles=contour_handles, loc='upper right')
        ax.add_artist(legend_contours)
        # Add SM and bestfit points
        sm_plot = ax.scatter([1.0], [0.0], marker="*", color='red', s=144, label='SM', zorder=10)
        bestfit_plot = ax.scatter(bestfit_kappaH, bestfit_kappaA, marker="P", color='white', edgecolors='black', s=144, linewidths=1, label='Best fit')
        ax.set_aspect("auto")
        ax.set_xlabel(r"$\kappa_\tau$")
        ax.set_ylabel(r"$\tilde{\kappa}_\tau$")
        ax.text(0.87, 0.04, r"$\mu$ = 1", transform=ax.transAxes, fontsize=16)
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        plt.tight_layout()
        ax.legend(handles=[sm_plot, bestfit_plot], loc='upper left')
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1, offset=0.0))
        hep.cms.label(ax=ax, label="", data=True, lumi='200', com='13 and 13.6', fontsize=18)
        plt.savefig(os.path.join('/'.join(args.file.split('/')[:-1]), "kappas_obs.pdf"))

    if args.mutautau:

        arrays = df.AsNumpy(["alpha", "mutautau", "nll"])
        alpha = arrays["alpha"]
        mutautau = arrays["mutautau"]
        nll = arrays["nll"]

        # interpolate NLL onto a fine grid
        x_grid = np.linspace(alpha.min(), alpha.max(), 3000)
        y_grid = np.linspace(mutautau.min(), mutautau.max(), 3000)
        X, Y = np.meshgrid(x_grid, y_grid)
        NLL_grid = griddata(points=(alpha, mutautau), values=nll, xi=(X, Y), method='cubic')

        # Get contours (using ROOT for NLL number)
        confidence = [0.683, 0.9545, 0.9973]
        levels = [ROOT.Math.chisquared_quantile_c(1 - cl, 2) for cl in confidence]

        print(f"Using NLL thresholds: 1sigma={levels[0]}, 2sigma={levels[1]}, 3sigma={levels[2]}")

        fig, ax = plt.subplots(figsize=(8,6.5))
        # Add NLL and contours
        im = ax.imshow(NLL_grid, origin='lower', extent=[X.min(), X.max(), Y.min(), Y.max()],cmap=cmap, vmin=0, vmax=sigma_5)
        plt.colorbar(im, label=r"$-2\Delta\ln \mathcal{L}$")
        contours = ax.contour(NLL_grid, levels=levels, colors='black', linestyles=['solid', 'dashdot', 'dashed'], origin='lower', extent=[x_grid.min(), x_grid.max(), y_grid.min(), y_grid.max()])
        # this is hacky but make legends for contours
        contour_handles = []
        for line, CL in zip(['solid', 'dashdot', 'dashed'], confidence):
            h, = ax.plot([], [], color='black', linestyle=line, label=f'{CL:.1%} CL')
            contour_handles.append(h)
        legend_contours = ax.legend(handles=contour_handles, loc='upper right')
        ax.add_artist(legend_contours)
        # Add SM and bestfit points
        sm_plot = ax.scatter([0.0], [1.0], marker="*", color='red', s=144, label='SM')
        bestfit_plot = ax.scatter(bestfit['alpha'], bestfit['mutautau'], marker="P", color='white', edgecolors='black', s=144, linewidths=1, label='Best fit')
        ax.set_aspect("auto")
        plt.xlabel(r"$\alpha^{H\tau\tau}$ (degrees)")
        plt.ylabel(r"$\mu$")
        plt.tight_layout()
        ax.legend(handles=[sm_plot, bestfit_plot], loc='upper left')
        ax.set_xticks([-90, -45, 0, 45, 90])
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        ax.set_xlim(-90, 90)
        # ax.yaxis.set_major_locator(ticker.MultipleLocator(1, offset=0.0))
        hep.cms.label(ax=ax, label="", data=True, lumi='200', com='13 and 13.6', fontsize=18)
        plt.savefig(os.path.join('/'.join(args.file.split('/')[:-1]), "mutautauVsalpha.pdf"))


    if args.muvsmu:

        arrays = df.AsNumpy(["muggH", "muV", "nll"])

        muggH = arrays["muggH"]
        muV = arrays["muV"]
        nll = arrays["nll"]

        # interpolate NLL onto a fine grid
        x_grid = np.linspace(muV.min(), muV.max(), 5000)
        y_grid = np.linspace(muggH.min(), muggH.max(), 5000)
        X, Y = np.meshgrid(x_grid, y_grid)

        NLL_grid = griddata(points=(muV, muggH), values=nll, xi=(X, Y), method='cubic')

        # Get contours (using ROOT for NLL number)
        confidence = [0.683, 0.9545, 0.9973]
        levels = [ROOT.Math.chisquared_quantile_c(1 - cl, 2) for cl in confidence]
        sigma_5 = 28.74370242616088
        sigma_4 = ROOT.Math.chisquared_quantile_c(1 - 0.9999367, 2)

        base = sns.color_palette("Blues_r", as_cmap=True)

        print(f"Using NLL thresholds: 1sigma={levels[0]}, 2sigma={levels[1]}, 3sigma={levels[2]}")

        fig, ax = plt.subplots(figsize=(8,6.5))
        # Add NLL and contours
        im = ax.imshow(NLL_grid, origin='lower', extent=[X.min(), X.max(), Y.min(), Y.max()],cmap=cmap, vmin=0, vmax=sigma_4)
        plt.colorbar(im, label=r"$-2\Delta\ln \mathcal{L}$")
        contours = ax.contour(NLL_grid, levels=levels, colors='black', linestyles=['solid', 'dashdot', 'dashed'], origin='lower', extent=[x_grid.min(), x_grid.max(), y_grid.min(), y_grid.max()])
        # this is hacky but make legends for contours
        contour_handles = []
        for line, CL in zip(['solid', 'dashdot', 'dashed'], confidence):
            h, = ax.plot([], [], color='black', linestyle=line, label=f'{CL:.1%} CL')
            contour_handles.append(h)
        legend_contours = ax.legend(handles=contour_handles, loc='upper right')
        ax.add_artist(legend_contours)
        # Add SM and bestfit points
        sm_plot = ax.scatter([1.0], [1.0], marker="*", color='red', s=144, label='SM')
        bestfit_plot = ax.scatter(bestfit['muV'], bestfit['muggH'], marker="P", color='white', edgecolors='black', s=144, linewidths=1, label='Best fit')
        ax.set_aspect("auto")
        plt.xlabel(r"$\mu_{qqH}$")
        plt.ylabel(r"$\mu_{ggH}$")
        plt.tight_layout()
        ax.legend(handles=[sm_plot, bestfit_plot], loc='lower left')
        if 'run2run3' in args.file:
            combination = True
        else:
            combination = False
        if combination:
            ax.set_xlim(-2, 3)
            ax.set_ylim(-1, 3)
        else:
            ax.set_xlim(-7.25, 4)
            ax.set_ylim(-1, 5)
        # ax.set_xticks([-90, -45, 0, 45, 90])
        # ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
        # ax.yaxis.set_major_locator(ticker.MultipleLocator(1, offset=0.0))
        # hep.cms.label(ax=ax, label="", data=True, lumi='62.4', com='13.6', fontsize=18)
        if combination:
            hep.cms.label(ax=ax, label="Supplementary", data=True, lumi='200', com='13 and 13.6', fontsize=18)
            plt.savefig(os.path.join('/'.join(args.file.split('/')[:-1]), "muggHVsmuqqH_combination.pdf"))
        else:
            hep.cms.label(ax=ax, label="Supplementary", data=True, lumi='62.4', com='13.6', fontsize=18)
            plt.savefig(os.path.join('/'.join(args.file.split('/')[:-1]), "muggHVsmuqqH_run3.pdf"))



if __name__ == "__main__":
    args = get_args()
    main(args)

