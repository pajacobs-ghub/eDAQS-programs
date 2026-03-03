# jm_ads131m04_plot.py
# Plotting functions for ADS131M04 data
# JM 2025-11-10

import numpy as np
import matplotlib.pyplot as plt
import struct

def plot_channels(result, show=True, save_filename=None):
    '''
    Plot all 4 channels from ADS131M04 data.
    
    Parameters:
    -----------
    result : dict
        Dictionary returned from fetch_SRAM_data() containing:
        - 'data': bytearray with sample data
        - 'nsamples_before_trigger': number of pre-trigger samples
        - 'nsamples_after_trigger': number of post-trigger samples
        - 'dt_us': sample period in microseconds
        - 'nchan': number of channels (should be 4)
        - 'trigger_mode': trigger mode string
        - 'first_sample_index': where trigger occurred
    show : bool
        If True, display the plot. Default True.
    save_filename : str, optional
        If provided, save the plot to this filename (e.g., 'plot.png')
    '''
    
    # Extract metadata
    data_bytes = result['data']
    n_pre = result['nsamples_before_trigger']
    n_post = result['nsamples_after_trigger']
    total_samples = n_pre + n_post
    dt_us = result['dt_us']
    nchan = result['nchan']
    trigger_mode = result['trigger_mode']
    
    # Unpack all samples into channels
    channels = [[] for _ in range(nchan)]
    for i in range(total_samples):
        offset = i * 16  # 4 channels × 4 bytes
        ch0, ch1, ch2, ch3 = struct.unpack('<4i', data_bytes[offset:offset+16])
        channels[0].append(ch0)
        channels[1].append(ch1)
        channels[2].append(ch2)
        channels[3].append(ch3)
    
    # Create time array in milliseconds
    time_ms = np.arange(total_samples) * dt_us / 1000.0
    
    # Define trigger time (where pre-trigger ends)
    trigger_time_ms = n_pre * dt_us / 1000.0
    
    # High contrast colors on black background
    # IBM color palette
    colors = ['#648fff',  # Bright green
              '#fe6100',  # Cyan
              '#785ef0',  # Magenta
              '#ffb000']  # Yellow
    
    # Create figure with black background
    plt.style.use('dark_background')
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    fig.patch.set_facecolor('black')
    
    # Plot each channel
    for i in range(nchan):
        axes[i].plot(time_ms, channels[i], color=colors[i], linewidth=0.8)
        axes[i].set_ylabel(f'Channel {i}\n(ADC counts)', color=colors[i], fontweight='bold')
        axes[i].grid(True, alpha=0.3, linestyle='--')
        axes[i].set_facecolor('#1a1a1a')  # Dark gray background for plots
        
        # Mark trigger position with vertical line
        if trigger_mode in ['internal', 'external']:
            axes[i].axvline(x=trigger_time_ms, color='red', linestyle='--', 
                          linewidth=2, alpha=0.7, label='Trigger')
            if i == 0:  # Only show legend on first subplot
                axes[i].legend(loc='upper right')
        
        # Color the y-axis tick labels to match the trace
        axes[i].tick_params(axis='y', colors=colors[i])
    
    # Set x-label only on bottom plot
    axes[-1].set_xlabel('Time (ms)', fontweight='bold', fontsize=12)
    
    # Overall title
    title = f'ADS131M04 Data - Trigger Mode: {trigger_mode}\n'
    title += f'Samples: {total_samples} ({n_pre} pre-trigger, {n_post} post-trigger) | dt: {dt_us:.2f} μs'
    fig.suptitle(title, fontsize=14, fontweight='bold', color='white')
    
    plt.tight_layout()
    
    # Save if filename provided
    if save_filename:
        plt.savefig(save_filename, facecolor='black', dpi=150)
        print(f"Plot saved to {save_filename}")
    
    # Show plot if requested
    if show:
        plt.show()
    
    return fig, axes


if __name__ == '__main__':
    # Test/example usage
    print("This module provides plotting functions for ADS131M04 data.")
    print("Import it and use: plot_channels(result)")
