from typing import Union
import numpy as np
from numpy.core.fromnumeric import size
from nr_phy_sync import nrSyncSignals
from nr_phy_sync import nrSSB
from pyphysim.modulators import OFDM


def decode_pss(received_data, ssb_dim):
    """Find SSB with highest crosscorrelation to undistorted PSS available in resource grid 
    and extract N_ID_2, k_ssb and l_ssb

    Args:
        received_data ([complex, complex]): 2D resource grid in which to search for SSB
        ssb_dim (struct): SSB dimensions and nu

    Returns:
        tuple: N_ID_2, k_ssb, l_ssb
    """
    rec_pss_sym = np.array(received_data)
    nid2_candidates = np.array([nrSyncSignals.pss(N_ID2 = n_id2) for n_id2 in range(3)])
    
    corr = np.zeros((3, received_data.shape[0], received_data.shape[1]), dtype=complex)
    
    for (i,pss_i) in enumerate(nid2_candidates):
        rgrid_mask = np.zeros(rec_pss_sym.shape, dtype=complex)
        rgrid_mask[:ssb_dim['k'], :ssb_dim['l']] += nrSSB.map_pss(pss_i, ssb_dim)
        
        for l in range(received_data.shape[1]):
            for k in range(received_data.shape[0]):
                corr[i, k, l] =np.multiply(
                    np.roll(
                        np.roll(rgrid_mask, l, axis=1),
                            k, axis=0),
                        rec_pss_sym.real).sum()
                    
                
    return  np.unravel_index(np.argmax(corr, axis=None), corr.shape)

def pss_coarse_time_frequency_corr(fft_size: int, received_data: Union[np.ndarray, list], threshold: float, threshold_filter_down_spampling_factor: int):
    '''
    todo doccccc
    fft_size >= 240
    returns nid2, 
    '''
    #filter idxs which are under given threshold for range of fftsize 
    can_idxs = np.array(range(len(received_data-fft_size)))
    for ind in range(0, len(can_idxs)):
        if np.average(received_data[ind:ind+fft_size:threshold_filter_down_spampling_factor]) < threshold:
            can_idxs[ind] = -1
    idxs = [can_idxs != -1]

    ofdm = OFDM(fft_size,0, fft_size)
    corr = np.zeros(shape=(3,fft_size-239, len(received_data)-fft_size+1),dtype=complex )
    for i_NID_2 in range(corr.shape[0]):
        pss_i_data = nrSyncSignals.pss(N_ID2 = i_NID_2)
        ssb_dim ={
            'k': fft_size,
            'l': 1
        }
        pss_i = nrSSB.map_pss(pss_i_data,ssb_dim)[:,0]
        for i_f_offs in range(corr.shape[1]):
            candidate = ofdm.modulate(#np.fft.ifft(#
                np.roll(pss_i,i_f_offs))
            for i_t_offs in range(corr.shape[2]):
                corr[i_NID_2,i_f_offs,i_t_offs] = np.abs(np.sum( np.square(received_data[i_t_offs:i_t_offs+len(candidate)]) - np.square(candidate)))
    
    return np.unravel_index(np.argmin(corr, axis=None), corr.shape)

def split_array_at_threshold():
    pass

def decode_sss(sss_data, nid2, ssb_dim):
    """Extract N_ID_1 through crosscorrelation

    Args:
        sss_data ([complex]): unmapped SSS
        N_ID2 (int): Cell ID sector
        ssb_dim (struct): SSB dimensions and nu

    Returns:
        int: N_ID_1
    """
    sss_candidates = np.array([nrSyncSignals.sss(
        N_ID1 = nid1,
        N_ID2 = nid2) for nid1 in range(336)])
    
    corr = np.zeros(len(sss_candidates),dtype=complex)
    
    for i,sss_i in enumerate(sss_candidates):
        corr[i] = np.multiply(sss_i, sss_data).sum()
    
    return max(np.unravel_index(np.argmax(corr, axis=None), corr.shape))
