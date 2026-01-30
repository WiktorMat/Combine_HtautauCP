import ROOT
import os

ROOT.gStyle.SetOptStat(0)

# directory containing variations
path_to_files = '/vols/cms/lcr119/offline/HiggsCP/CMSSW_14_1_0_pre4/src/CombineHarvester/Combine_HtautauCP/outputs/Jan26_Baseline/cmb/common'

# Create canvas
c = ROOT.TCanvas("c", "c", 800, 800)
c.Divide(1, 2)

# Adjust pad sizes
topPad = c.GetPad(1)
ratioPad = c.GetPad(2)

topPad.SetPad(0.0, 0.20, 1.0, 1.0)
ratioPad.SetPad(0.0, 0.00, 1.0, 0.20)
ratioPad.SetGridy()


# systematics_to_check = ['CMS_pileup', 'CMS_HIG25012_scale_t_DM1PNet_2022EE', 'CMS_HIG25012_scale_t_DM10PNet_2022EE', 'CMS_scale_j_Absolute_2022EE', 'CMS_res_j_2022EE']
systematics_to_check = ['CMS_pileup']
# processes_to_check = ['signal', 'ZTT']
processes_to_check = ['ZTT'] #, 'JetFakes']

for systematic_to_check in systematics_to_check:

    output_pdf = f'syst_checks_Unblinding/check_vars_{systematic_to_check}.pdf'
    # Open the multipage PDF
    c.Print(output_pdf + "[")


    for process in processes_to_check:
        print(f"Checking process: {process}")
        print('-'*100)
        for file in sorted(os.listdir(path_to_files)):
            if not file.endswith(".root"):
                continue
            print(f"Processing: {file}")

            root_file = ROOT.TFile.Open(os.path.join(path_to_files, file))
            directory = file.split("_input")[0]

            if process == 'signal':
                # add together the higgs processes
                signals = ['ggH_sm_prod_sm_htt125', 'qqH_sm_htt125', 'WH_sm_htt125', 'ZH_sm_htt125']
                for i, signal in enumerate(signals):
                    # add together all histos
                    h_nom_s = root_file.Get(f"{directory}/{signal}")
                    h_up_s = root_file.Get(f"{directory}/{signal}_{systematic_to_check}Up_sym")
                    h_down_s = root_file.Get(f"{directory}/{signal}_{systematic_to_check}Down_sym")

                    if not h_up_s or not h_down_s or not h_nom_s:
                        print("Warning: Missing one or more histograms, skipping this variation: " + f"{directory}/{signal}" + f" for syst: {systematic_to_check}")
                        histo_nom = h_nom_s
                        histo_up   = h_up_s
                        histo_down = h_down_s
                        continue

                    if i == 0:
                        histo_nom = h_nom_s.Clone("histo_nom")
                        histo_up   = h_up_s.Clone("histo_up")
                        histo_down = h_down_s.Clone("histo_down")
                    else:
                        histo_nom.Add(h_nom_s)
                        histo_up.Add(h_up_s)
                        histo_down.Add(h_down_s)
            else:
                histo_nom = root_file.Get(f"{directory}/{process}")
                histo_up   = root_file.Get(f"{directory}/{process}_{systematic_to_check}Up")
                histo_down = root_file.Get(f"{directory}/{process}_{systematic_to_check}Down")

            # if not histo_nom:
            #     raise ValueError(f"Missing nominal histogram in {file} for {process}")
            #     continue

            # if not histo_up:
            #     print(f" WARNING: Missing Up histogram: {directory}/{process}_{systematic_to_check}Up")
            # if not histo_down:
            #     print(f"WARNING: Missing Down histogram: {directory}/{process}_{systematic_to_check}Down")

            if not histo_up or not histo_down or not histo_nom:
                print("Warning: Missing one or more histograms, skipping this variation: " + f"{directory}/{process}" + f" for syst: {systematic_to_check}")
                continue

            # to avoid double countin stat uncert, divide here
            histo_nom_ratio = histo_nom.Clone("histo_nom_ratio")
            for i in range(1, histo_nom.GetNbinsX() + 1):
                histo_nom_ratio.SetBinError(i, 0.0) # zero stat uncer.

            ratio_up = histo_up.Clone("ratio_up")
            ratio_up.Divide(histo_nom_ratio)

            ratio_down = histo_down.Clone("ratio_down")
            ratio_down.Divide(histo_nom_ratio)

            # Main plot
            topPad.cd()
            histo_nom.SetTitle("")


            if 'tt_6' in directory:
                ch_label = 'a_{1}^{3pr}a_{1}^{3pr}'
            elif 'tt_11' in directory:
                ch_label = 'a_{1}^{1pr}a_{1}^{3pr}'
            elif 'tt_10' in directory:
                ch_label = '#pi a_{1}^{1pr}'
            elif 'tt_7' in directory:
                ch_label = '#pi#rho'
            elif 'tt_4' in directory:
                ch_label = '#rho a_{1}^{1pr}/a_{1}^{1pr}a_{1}^{1pr}'
            elif 'tt_9' in directory:
                ch_label = '#pi a_{1}^{3pr}'
            elif 'tt_8' in directory:
                ch_label = '#pi#pi'
            elif 'tt_3' in directory:
                ch_label = '#rho#rho'
            elif 'tt_5' in directory:
                ch_label = '#rho a_{1}^{3pr}'
            elif 'et_6' in directory:
                ch_label = 'ea_{1}^{1pr}'
            elif 'et_3' in directory:
                ch_label = 'e#rho'
            elif 'et_5' in directory:
                ch_label = 'ea_{1}^{3pr}'
            elif 'et_4' in directory:
                ch_label = 'e#pi'
            elif 'mt_6' in directory:
                ch_label = '#mua_{1}^{1pr}'
            elif 'mt_3' in directory:
                ch_label = '#mu#rho'
            elif 'mt_5' in directory:
                ch_label = '#mua_{1}^{3pr}'
            elif 'mt_4' in directory:
                ch_label = '#mu#pi'
            elif 'tt_2' in directory:
                ch_label = '#tau_{h}#tau_{h} genuine background'
            elif 'tt_2' in directory:
                ch_label = '#tau_{h}#tau_{h} fake background'
            elif 'mt_1' in directory:
                ch_label = '#mu#tau_{h} genuine background'
            elif 'mt_2' in directory:
                ch_label = '#mu#tau_{h} fake background'
            elif 'et_1' in directory:
                ch_label = 'e#tau_{h} genuine background'
            elif 'et_2' in directory:
                ch_label = 'e#tau_{h} fake background'


            histo_nom.GetXaxis().SetTitle(ch_label)

            histo_nom.SetLineColor(ROOT.kBlack)
            histo_up.SetLineColor(ROOT.kRed)
            histo_down.SetLineColor(ROOT.kBlue)

            histo_nom.SetLineWidth(2)
            histo_up.SetLineWidth(2)
            histo_down.SetLineWidth(2)

            histo_nom.Draw("E1")
            histo_up.Draw("E1 same")
            histo_down.Draw("E1 same")

            # Title
            title = ROOT.TLatex()
            title.SetTextSize(0.045)
            title.SetNDC()
            title.DrawLatex(0.12, 0.93, f"{process}   ({systematic_to_check})")

            # Legend
            legend = ROOT.TLegend(0.65, 0.70, 0.88, 0.88)
            legend.SetBorderSize(1)
            legend.SetFillColor(0)
            legend.SetTextSize(0.03)
            legend.AddEntry(histo_nom,  "Nominal", "l")
            legend.AddEntry(histo_up,   "Up", "l")
            legend.AddEntry(histo_down, "Down", "l")
            legend.Draw()

            ratioPad.cd()
            ratio_up.SetTitle("")
            ratio_up.SetLineColor(ROOT.kRed)
            ratio_down.SetLineColor(ROOT.kBlue)
            ratio_up.SetLineWidth(2)
            ratio_down.SetLineWidth(2)

            ratio_up.GetYaxis().SetTitle("Var / Nom")
            ratio_up.GetYaxis().SetTitleSize(0.10)
            ratio_up.GetYaxis().SetTitleOffset(0.5)
            ratio_up.GetYaxis().SetLabelSize(0.08)
            ratio_up.GetXaxis().SetTitleSize(0.10)
            ratio_up.GetXaxis().SetLabelSize(0.08)
            # ratio_up.SetMinimum(0.7)
            # ratio_up.SetMaximum(1.3)

            # choose y axes limits
            ymin = float("inf")
            ymax = float("-inf")
            for h in [ratio_up, ratio_down]:
                for i in range(1, h.GetNbinsX() + 1):
                    val = h.GetBinContent(i)
                    err = h.GetBinError(i)
                    if val == 0:
                        continue
                    ymin = min(ymin, val - err)
                    ymax = max(ymax, val + err)

            # Fallback in case something went wrong
            if ymin == float("inf") or ymax == float("-inf"):
                ymin, ymax = 0.9, 1.1

            max_dev = max(abs(ymax - 1.0), abs(1.0 - ymin))
            ymin = 1.0 - max_dev
            ymax = 1.0 + max_dev
            ratio_up.SetMinimum(ymin)
            ratio_up.SetMaximum(ymax)

            ratio_up.Draw("E")
            ratio_down.Draw("E1 same")

            # Horizontal line at 1.0
            line = ROOT.TLine(
                ratio_up.GetXaxis().GetXmin(), 1.0,
                ratio_up.GetXaxis().GetXmax(), 1.0
            )
            line.SetLineStyle(2)
            line.Draw()

            c.Print(output_pdf)

        root_file.Close()
        print("*"*100)

    c.Print(output_pdf + "]")
    print("Saved:", output_pdf)
