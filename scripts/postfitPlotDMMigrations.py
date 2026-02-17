import CombineHarvester.CombineTools.plotting as plot
import ROOT
import argparse
import math
import ctypes
from scipy.stats import chi2
import os

ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.AddDirectory(False)

def getHistogram(fname, histname, dirname='', allowEmpty=False):
    outname = fname.GetName()
    for key in fname.GetListOfKeys():
        histo = fname.Get(key.GetName())
        dircheck = False
        if dirname == '' : dircheck=True
        elif dirname in key.GetName(): dircheck=True
        if isinstance(histo,ROOT.TH1F) and key.GetName()==histname:
            return [histo,outname]
        elif isinstance(histo,ROOT.TDirectory) and dircheck:
            return getHistogram(histo,histname, allowEmpty=allowEmpty)
    print('Failed to find histogram with name %(histname)s in file %(fname)s '%vars())
    if allowEmpty:
        return [ROOT.TH1F('empty', '', 1, 0, 1), outname]
    else:
        return None

def backgroundComp(leg,plots,colour):
    return dict([('leg_text',leg),('plot_list',plots),('colour',colour)])

def createAxisHists(n,src,xmin=0,xmax=499):
    result = []
    for i in range(0,n):
        res = src.Clone()
        res.Reset()
        res.SetTitle("")
        res.SetName("axis%(i)d"%vars())
        res.SetAxisRange(xmin,xmax)
        res.SetStats(0)
        result.append(res)
    return result

def PositionedLegendUnrolled(width, height, pos, offset):
    o = offset
    w = width
    h = height
    l = ROOT.gPad.GetLeftMargin()
    t = ROOT.gPad.GetTopMargin()
    b = ROOT.gPad.GetBottomMargin()
    r = ROOT.gPad.GetRightMargin()
    if pos == 1:
        return ROOT.TLegend(l + o, 1 - t - o - h, l + o + w, 1 - t - o, '', 'NBNDC')
    if pos == 2:
        c = l + 0.5 * (1 - l - r)
        return ROOT.TLegend(c - 0.5 * w, 1 - t - o - h, c + 0.5 * w, 1 - t - o, '', 'NBNDC')
    if pos == 3:
        return ROOT.TLegend(1 - r - o - w, 1 - t - o - h, 1 - r - o, 1 - t - o, '', 'NBNDC')
    if pos == 4:
        return ROOT.TLegend(l + o, b + o, l + o + w, b + o + h, '', 'NBNDC')
    if pos == 5:
        c = l + 0.5 * (1 - l - r)
        return ROOT.TLegend(c - 0.5 * w, b + o, c + 0.5 * w, b + o + h, '', 'NBNDC')
    if pos == 6:
        return ROOT.TLegend(1 - r - o - w, b + o, 1 - r - o, b + o + h, '', 'NBNDC')
    if pos == 7:
        return ROOT.TLegend(1 - o - w, 1 - t - o - h, 1 - o, 1 - t - o, '', 'NBNDC')

def DrawTitleUnrolled(pad, text, align, scale=1):
    pad_backup = ROOT.gPad
    pad.cd()
    t = pad.GetTopMargin()
    l = pad.GetLeftMargin()
    r = pad.GetRightMargin()

    pad_ratio = (float(pad.GetWh()) * pad.GetAbsHNDC()) / \
        (float(pad.GetWw()) * pad.GetAbsWNDC())
    if pad_ratio < 1.:
        pad_ratio = 1.

    textSize = 0.6
    textOffset = 0.2

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextFont(42)
    latex.SetTextSize(textSize * t * pad_ratio * scale)

    y_off = 1 - t + textOffset * t + 0.01
    if align == 1:
        latex.SetTextAlign(11)
        latex.DrawLatex(l, y_off, text)
    if align == 2:
        latex.SetTextAlign(21)
        latex.DrawLatex(l + (1 - l - r) * 0.5, y_off, text)
    if align == 3:
        latex.SetTextAlign(31)
        latex.DrawLatex(1 - r, y_off, text)
    pad_backup.cd()

def garwood_interval(n, cl=0.683):
    """
    Compute Garwood interval (exact Poisson confidence interval).
    Returns (low, high) for observed count n.
    """
    alpha = 1 - cl
    if n == 0:
        low = 0.0
    else:
        low = 0.5 * chi2.ppf(alpha / 2, 2 * n)
    high = 0.5 * chi2.ppf(1 - alpha / 2, 2 * (n + 1))
    return low, high

def MakeRatioGraph(num,denom):
    # make a ratio graph from a TGraphAsymmErrors and a TH1
    ratio = num.Clone()
    for i in range(0, ratio.GetN()):
        x = ctypes.c_double(0.)
        y = ctypes.c_double(0.)
        ratio.GetPoint(i, x, y)
        x = x.value
        y = y.value
        bin = denom.FindBin(x)
        denom_y = denom.GetBinContent(bin)
        if denom_y != 0:
            ratio.SetPoint(i, x, y/denom_y)
            # keep the relative errors the same
            y_high = ratio.GetErrorYhigh(i)/denom_y
            y_low = ratio.GetErrorYlow(i)/denom_y
            ratio.SetPointError(i, ratio.GetErrorXlow(i), ratio.GetErrorXhigh(i), y_low, y_high)
        else:
            ratio.SetPoint(i, x, 0)
            ratio.SetPointError(i, 0., 0., 0., 0.)
    return ratio

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Post-fit plot script for Htautau CP analysis')
    parser.add_argument('--input_file', '-i',  type=str, default='shapes_postfit_incTES.root',
                        help='Input ROOT file containing histograms')
    parser.add_argument('--input_file_ps', type=str,
                        help='Input ROOT file containing pseudoscalar histograms (optional)')
    parser.add_argument('--bin_name', '-b', type=str, default='htt_tt_3_13p6TeV',
                        help='Name of the bin to plot')
    parser.add_argument('--norm_bins', action='store_true',
                        help='Normalize bins to bin width')
    parser.add_argument('--lumi', type=str, default='62.4 fb^{-1} (13.6 TeV)',
                        help='Luminosity label for the plot')
    parser.add_argument('--dir', type=str, default="",
                        help='Output directory for the plots')
    parser.add_argument('--prefit', action='store_true',
                        help='prefit_plot')

    args = parser.parse_args()

    # these can eventually be set by command line arguments:
    lumi = args.lumi
    bin_name = args.bin_name
    channel = bin_name[4:6]


    if 'mt_1' in bin_name:
        ch_label = 'DM=0'
    elif 'mt_2' in bin_name:
        ch_label = 'DM=1'
    elif 'mt_3' in bin_name:
        ch_label = 'DM=2'
    elif 'mt_4' in bin_name:
        ch_label = 'DM=10'


    input_file = ROOT.TFile(args.input_file)
   
    if args.input_file_ps:
        input_file_ps = ROOT.TFile(args.input_file_ps)
    else: input_file_ps = None
    norm_bins = args.norm_bins
    
    if norm_bins:
        y_title = 'Events / bin width'
    else: 
        y_title = 'Events'

    ratio_range = '0.75,1.25'


    plot.ModTDRStyle(width=900, height=800, r=0.3, l=0.15)
    x_title = 'm_{#tau} [GeV]'

    logy = False
    extra_pad = 0.15
    
    canv = ROOT.TCanvas()    
    pads=plot.TwoPadSplit(0.35,0.01,0.01)
    
    bkghist = getHistogram(input_file,'TotalProcs',bin_name)[0]
    
    datahist = getHistogram(input_file,"data_obs",bin_name)[0]
    if norm_bins:
        datahist.Scale(1.0,"width")
    datahist.SetMarkerStyle(20)
    

    #convert datahist into datagraph using TGraphAsymmErrors for proper Poissonian error bars
    datagraph = ROOT.TGraphAsymmErrors(datahist)
    datagraph.SetName("data_obs_graph")

    for i in range(0, datagraph.GetN()):
        x = ctypes.c_double(0.)
        y = ctypes.c_double(0.)
        datagraph.GetPoint(i, x, y)
        x = x.value
        y = y.value
        x_err_low = datagraph.GetErrorXlow(i)
        x_err_high = datagraph.GetErrorXhigh(i)
        if y < 0:
            datagraph.SetPoint(i, x, 0)
            datagraph.SetPointError(i, x_err_low, x_err_high, 0., 0.)
        else:
            low, high = garwood_interval(int(y), cl=0.683)
            datagraph.SetPointError(i, x_err_low, x_err_high, y - low, high - y)
    datahist = datagraph
    
    bkghist.SetMarkerSize(0)
    bkghist.SetFillColor(2001)
    bkghist.SetLineColor(0)
    bkghist.SetLineWidth(1)
    bkghist.SetFillColor(plot.CreateTransparentColor(12,0.4))
    if norm_bins: 
        bkghist.Scale(1.0,"width")
    
    background_schemes = {
        'mt':[
                backgroundComp("Backgrounds",["ZL","ZJ","VVT","VVJ","TTT","TTJ","QCD","W"],ROOT.TColor.GetColor(100,192,232)),
                backgroundComp("Z#rightarrow#tau#tau (#tau#rightarrow other)",["ZTT_other"],ROOT.TColor.GetColor(150,100,50)), # brown
                backgroundComp("Z#rightarrow#tau#tau (#tau#rightarrow a1^{1pr})",["ZTT_a11pr"],ROOT.TColor.GetColor(255,0,0)), # red
                backgroundComp("Z#rightarrow#tau#tau (#tau#rightarrow#pi)",["ZTT_pi"],ROOT.TColor.GetColor(160,193,114)), # green
                backgroundComp("Z#rightarrow#tau#tau (#tau#rightarrow a1^{3pr})",["ZTT_a13pr"],ROOT.TColor.GetColor(51,51,230)), # dark blue
                backgroundComp("Z#rightarrow#tau#tau (#tau#rightarrow#rho)",["ZTT_rho"],ROOT.TColor.GetColor(255,169,14)) # yellow
                ]
    }


    stack_histos = []
    
    for t in background_schemes[channel]:
        plots = t['plot_list']
        isHist = False
        h = ROOT.TH1F()
        for k in plots:
            if h.GetEntries()==0 and getHistogram(input_file,k, bin_name,False) is not None:
                isHist = True
                h = getHistogram(input_file,k, bin_name)[0]
                h.SetName(k)
            else:
                if getHistogram(input_file,k, bin_name,False) is not None:
                    isHist = True
                    h.Add(getHistogram(input_file,k, bin_name)[0])
    
        h.SetFillColor(t['colour'])
        h.SetLineColor(ROOT.kBlack)
        h.SetMarkerSize(0)
        
        if norm_bins: h.Scale(1.0,"width")
        if isHist:
            stack_histos.append(h)
    
    stack = ROOT.THStack("hs","")
    for hists in stack_histos:
        stack.Add(hists)
    
    axish = createAxisHists(2,bkghist,bkghist.GetXaxis().GetXmin(),bkghist.GetXaxis().GetXmax()-0.01)

    axish[0].SetMaximum(bkghist.GetMaximum())
    # axish[0].SetMaximum(bkghist.GetMaximum())
    axish[0].GetYaxis().SetTitle(y_title)
    axish[0].GetXaxis().SetLabelSize(0)
    axish[0].GetXaxis().SetTitleSize(0)
    axish[1].GetXaxis().SetTitle(x_title)
    
    
    pads[0].cd()
    pads[0].SetTicks(1)
    if logy:
        pads[0].SetLogy()
        axish[0].SetMinimum(0.01)
    
        #axish[0].SetMinimum(0.01)
    axish[0].Draw("hist")
    
    stack.Draw("histsame")
    bkghist.Draw("e2same")
    datahist.Draw("P Z 0 same")

    pads[0].RedrawAxis()
    
    # now we produce the ratio plot
    # For now the ratio just shows the ratio of the observed data to the signal+background expectation
    # this can be changed in the future to show the ratio to background only and signal+background etc seperatly 
    
    pads[1].cd()
    pads[1].SetTicks(1)
    pads[1].SetGrid(0,1)
    axish[1].Draw("axis")
    axish[1].SetMinimum(float(ratio_range.split(',')[0]))
    axish[1].SetMaximum(float(ratio_range.split(',')[1]))
    axish[1].GetYaxis().SetTitle("Obs./Exp.")
    # draw dashed line at 1
    line = ROOT.TLine(axish[1].GetXaxis().GetXmin(), 1, axish[1].GetXaxis().GetXmax(), 1)
    line.SetLineStyle(2)
    line.SetLineColor(ROOT.kBlack)
    line.Draw("same")
    
    ratio_bkghist = plot.MakeRatioHist(bkghist,bkghist,True,False)
    ratio_bkghist.Draw("e2same")
    if isinstance(datahist,ROOT.TGraphAsymmErrors):
        ratio_datahist = MakeRatioGraph(datahist,bkghist)
    else:
        ratio_datahist = plot.MakeRatioHist(datahist,bkghist,True,False)
    ratio_datahist.Draw("P Z 0 same")

    pads[1].RedrawAxis()

    # draw the title, labels, and legend
    
    #CMS and lumi labels

    plot.FixTopRange(pads[0], plot.GetPadYMax(pads[0]), extra_pad if extra_pad>0 else 0.15)
    extra=''
    plot.DrawCMSLogo(pads[0], 'CMS', extra, 0, 0.17, -0.0, 2.0, '', 0.85)
    plot.DrawTitle(pads[0], ch_label + "   " + lumi, 3, textSize=0.6)

    legend = PositionedLegendUnrolled(0.25,0.5,7,0.)
    legend.SetTextSize(0.03) 
    legend.SetTextFont(42)
    legend.SetFillStyle(0)
    
    legend.AddEntry(datahist,"Observed","PEl")
    # loop backwards over the stack_histos by index to add them in the right order
    for legi in range(len(stack_histos)-1,-1,-1):
        hists = stack_histos[legi]
        legend.AddEntry(hists,background_schemes[channel][legi]['leg_text'],"f")
    
    legend.AddEntry(bkghist,"Uncertainty","f")

    legend.Draw("same")
    
    canv.Print(os.path.join(args.dir, bin_name + '.pdf'))
    canv.Print(os.path.join(args.dir, bin_name + '.png'))
    
