nominal_histograms = {} # store nominal histos in this dictionary (for zeroing systs)

def green(string,**kwargs):
    '''Displays text in green text inside a black background'''
    return kwargs.get('pre',"")+"\x1b[0;32;40m%s\033[0m"%string

def NegativeBins(p):
    '''Replaces negative bins in hists with 0'''
    hist = p.shape().Clone()
    for i in range(1,hist.GetNbinsX()+1):
        if hist.GetBinContent(i) < 0:
            print("(Process, Channel, Bin) = (%s, %s, %s) has negative bins." % (p.process(), p.channel(), p.bin()))
            hist.SetBinContent(i,0)
    p.set_shape(hist,False)


def GetNominalHisto(p):
    print(f"Retrieving nominal histogram for process: {p.process()} and category: {p.bin()}")
    nom_hist = p.shape().Clone()
    nominal_histograms[p.process()+'_'+p.bin()] = nom_hist


def ZeroNegativeBins(hist, name, type='up/down'):
    '''Sets negative bins in a histogram to zero'''
    integral_before = hist.Integral()
    negative_bins = False
    for i in range(1, hist.GetNbinsX() + 1):
        if hist.GetBinContent(i) < 0:
            negative_bins = True
            hist.SetBinContent(i, 0)
    # update integral
    integral_after = hist.Integral()
    if integral_after > 0:
        hist.Scale(integral_before/integral_after)
    return negative_bins, hist

def DetectNegativeSyst(s):
    '''Replaces negative bins in hists with 0'''
    is_shape = s.type() == 'shape'
    if is_shape:
        up_histo = s.shape_u().Clone()
        down_histo = s.shape_d().Clone()
        is_neg_up, new_up_histo = ZeroNegativeBins(up_histo, s.name(), 'up')
        is_neg_down, new_down_histo = ZeroNegativeBins(down_histo, s.name(), 'down')
        if is_neg_up or is_neg_down:
            print(f">>>>> Negative bins found for systematic: {s.name()} for process: {s.process()} and category: {s.bin()}")
            nominal_hist = nominal_histograms[s.process()+'_'+s.bin()].Clone()
            s.set_shapes(new_up_histo, new_down_histo, nominal_hist)

def NegativeYields(p):
    '''If process has negative yield then set to 0'''
    if p.rate()<0:
        print("(Process, Channel, Bin) = (%s, %s, %s) has a negative yield" % (p.process(), p.channel(), p.bin()))
        p.set_rate(0.)
