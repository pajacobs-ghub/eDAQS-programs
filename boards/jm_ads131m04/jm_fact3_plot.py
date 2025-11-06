# jm_fact3_plot.py
# Real-time plotting of voltage data from the ADS131M04
# This script continuously reads voltage data and plots it using matplotlib
#
# 2025-11-06    First version

import sys
sys.path.append("../..")
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
from daq_mcu.pico2_ads131m04 import PICO2_ADS131M04_DAQ


class RealtimeVoltageMonitor:
    def __init__(self, daq, max_points=1000, interval=15):
        """
        Initialize the real-time voltage monitor.
        
        Args:
            daq: PICO2_ADS141M04_DAQ instance
            max_points: Maximum number of points to display (default 1000)
            interval: Update interval in milliseconds (default 50ms = 20Hz)
        """
        self.daq = daq
        self.max_points = max_points
        self.interval = interval
        
        # Create data buffers for 2 channels (2 and 3)
        self.time_data = deque(maxlen=max_points)
        self.ch2_data = deque(maxlen=max_points)
        self.ch3_data = deque(maxlen=max_points)
        
        self.start_time = time.time()
        self.sample_count = 0
        
        # Setup the plot
        self.setup_plot()
        
    def setup_plot(self):
        """Setup the matplotlib figure and axes."""
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 6))
        self.fig.suptitle('ADS131M04 Real-Time Voltage Monitor', fontsize=14, fontweight='bold')
        
        # Create line objects for channels 2 and 3
        self.lines = []
        channel_names = ['Channel 2', 'Channel 3']
        colors = ['green', 'orange']
        
        for i, (ax, name, color) in enumerate(zip(self.axes, channel_names, colors)):
            line, = ax.plot([], [], color=color, linewidth=1.5, label=name)
            self.lines.append(line)
            
            ax.set_ylim(-0.2, 0.1)  # Fixed y-axis from -1.5V to +1.5V
            ax.set_ylabel('Voltage (V)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right')
            
            # Add horizontal line at 0V
            ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
        
        self.axes[-1].set_xlabel('Time (s)', fontsize=10)
        
        # Add text for sample rate display
        self.sample_rate_text = self.fig.text(0.02, 0.02, '', fontsize=10)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
    def init_animation(self):
        """Initialize animation - required by FuncAnimation."""
        for line in self.lines:
            line.set_data([], [])
        return self.lines
    
    def update_plot(self, frame):
        """Update function called by animation."""
        try:
            # Get voltage data
            voltages = self.daq.single_sample_as_volts(vref=1.2, gain=1)
            
            # Update time
            current_time = time.time() - self.start_time
            self.time_data.append(current_time)
            
            # Update channel data (only channels 2 and 3)
            self.ch2_data.append(voltages[2])
            self.ch3_data.append(voltages[3])
            
            self.sample_count += 1
            
            # Update plot data
            time_array = np.array(self.time_data)
            data_arrays = [
                np.array(self.ch2_data),
                np.array(self.ch3_data)
            ]
            
            for line, data in zip(self.lines, data_arrays):
                line.set_data(time_array, data)
            
            # Update x-axis limits to show latest data
            if len(self.time_data) > 0:
                for ax in self.axes:
                    if current_time > 10:  # Show 10 second window
                        ax.set_xlim(current_time - 10, current_time)
                    else:
                        ax.set_xlim(0, max(10, current_time))
            
            # Calculate and display sample rate
            if current_time > 0:
                sample_rate = self.sample_count / current_time
                self.sample_rate_text.set_text(f'Sample Rate: {sample_rate:.1f} Hz | Samples: {self.sample_count}')
            
        except Exception as e:
            print(f"Error updating plot: {e}")
        
        return self.lines
    
    def start(self):
        """Start the animation."""
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update_plot,
            init_func=self.init_animation,
            interval=self.interval,
            blit=False,
            cache_frame_data=False
        )
        plt.show()


def main(sp, node_id, vref=1.2, gain=1, interval=50):
    """
    Main function to setup and start the monitor.
    
    Args:
        sp: Serial port object
        node_id: Node identifier
        vref: Reference voltage in volts (default 1.2V)
        gain: PGA gain setting (default 1)
        interval: Update interval in milliseconds (default 50ms)
    """
    print("SUPER-ADC ADS131M04 Real-Time Voltage Monitor")
    print("=" * 50)
    
    node1 = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
    daq = PICO2_ADS131M04_DAQ(node1)
    
    print(f"COMMS MCU: {node1.get_version()}")
    print(f"DAQ MCU:   {daq.get_version()}")
    print(f"Settings:  VREF={vref}V, Gain={gain}, Update={1000/interval:.1f}Hz")
    print()
    print("Resetting registers...")
    print(daq.reset_registers())
    
    # Test a single sample
    print("\nTesting initial sample:")
    voltages = daq.single_sample_as_volts(vref=vref, gain=gain)
    print(f"  CH0: {voltages[0]:+.6f} V")
    print(f"  CH1: {voltages[1]:+.6f} V")
    print(f"  CH2: {voltages[2]:+.6f} V")
    print(f"  CH3: {voltages[3]:+.6f} V")
    
    print("\nStarting real-time plot...")
    print("Close the plot window to exit.")
    
    # Create and start the monitor
    monitor = RealtimeVoltageMonitor(daq, max_points=1000, interval=interval)
    monitor.start()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time voltage monitor for ADS131M04",
        epilog='Close the plot window or use Ctrl-C to stop.'
    )
    parser.add_argument('-p', '--port', dest='port', default='/dev/ttyUSB0',
                        help='Serial port name (default: /dev/ttyUSB0)')
    parser.add_argument('-i', '--identity', dest='identity', default='C',
                        help='Node identity character (default: C)')
    parser.add_argument('--vref', type=float, default=1.2,
                        help='Reference voltage in volts (default: 1.2)')
    parser.add_argument('--gain', type=int, default=1, choices=[1, 2, 4, 8, 16, 32, 64, 128],
                        help='PGA gain setting (default: 1)')
    parser.add_argument('--interval', type=int, default=50,
                        help='Update interval in milliseconds (default: 50)')
    
    args = parser.parse_args()
    
    sp = rs485.openPort(args.port)
    if sp:
        try:
            main(sp, args.identity, vref=args.vref, gain=args.gain, interval=args.interval)
        except KeyboardInterrupt:
            print("\n\nStopped by user.")
        finally:
            sp.close()
    else:
        print("Could not open serial port.")
    
    print("Done.")
