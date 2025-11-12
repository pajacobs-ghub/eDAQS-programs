# jm_fact3_plot2_dpg.py
# Real-time plotting of voltage data from the ADS131M04 and FACT3 amplifier hat.
# This script continuously reads voltage data and plots it using DearPyGui
# DearPyGui is much faster than matplotlib for real-time plotting
#
# 2025-11-09    Refactored from matplotlib to DearPyGui

import sys
sys.path.append("../..")
import time
import threading
from collections import deque
import dearpygui.dearpygui as dpg
from comms_mcu import rs485
from comms_mcu.pic18f16q41_jm_ads131m04_comms import PIC18F16Q41_JM_ADS131M04_COMMS
from daq_mcu.pico2_ads131m04 import PICO2_ADS131M04_DAQ


class RealtimeVoltageMonitorDPG:
    def __init__(self, daq, max_points=1000):
        """
        Initialize the real-time voltage monitor.
        
        Args:
            daq: PICO2_ADS131M04_DAQ instance
            max_points: Maximum number of points to display (default 1000)
        """
        self.daq = daq
        self.max_points = max_points
        
        # Create data buffers for 2 channels (2 and 3)
        self.time_data = deque(maxlen=max_points)
        self.ch2_data = deque(maxlen=max_points)
        self.ch3_data = deque(maxlen=max_points)
        
        self.start_time = time.time()
        self.sample_count = 0
        self.running = True
        self.paused = False
        
        # Create DearPyGui context
        dpg.create_context()
        
    def setup_gui(self):
        """Setup the DearPyGui window and plots."""
        
        # Setup window
        with dpg.window(label="ADS131M04 Real-Time Voltage Monitor", 
                       tag="main_window", width=1200, height=700):
            
            # Control buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Pause/Resume", callback=self.toggle_pause)
                dpg.add_button(label="Reset", callback=self.reset_data)
                dpg.add_text("", tag="status_text")
            
            dpg.add_separator()
            
            # Channel 2 plot
            with dpg.plot(label="Channel 2", height=280, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="ch2_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (V)", tag="ch2_y_axis")
                
                # Set y-axis limits
                dpg.set_axis_limits("ch2_y_axis", -0.3, 0.3)
                
                # Add horizontal line at 0V
                dpg.add_line_series([0, 10], [0, 0], label="0V Reference", 
                                   parent="ch2_y_axis", tag="ch2_zero_line")
                
                # Add data series
                dpg.add_line_series([], [], label="Channel 2", 
                                   parent="ch2_y_axis", tag="ch2_series")
            
            dpg.add_separator()
            
            # Channel 3 plot
            with dpg.plot(label="Channel 3", height=280, width=-1):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)", tag="ch3_x_axis")
                dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (V)", tag="ch3_y_axis")
                
                # Set y-axis limits
                dpg.set_axis_limits("ch3_y_axis", -1.3, 1.3)
                
                # Add horizontal line at 0V
                dpg.add_line_series([0, 10], [0, 0], label="0V Reference", 
                                   parent="ch3_y_axis", tag="ch3_zero_line")
                
                # Add data series
                dpg.add_line_series([], [], label="Channel 3", 
                                   parent="ch3_y_axis", tag="ch3_series")
        
        # Setup viewport
        dpg.create_viewport(title="ADS131M04 Monitor", width=1280, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        status = "PAUSED" if self.paused else "RUNNING"
        print(f"Status: {status}")
        
    def reset_data(self):
        """Reset all data buffers."""
        self.time_data.clear()
        self.ch2_data.clear()
        self.ch3_data.clear()
        self.start_time = time.time()
        self.sample_count = 0
        print("Data reset")
        
    def acquisition_thread(self):
        """Background thread for data acquisition."""
        while self.running:
            if not self.paused:
                try:
                    # Get voltage data
                    voltages = self.daq.single_sample_as_volts()
                    
                    # Update time
                    current_time = time.time() - self.start_time
                    
                    # Add data to buffers
                    self.time_data.append(current_time)
                    self.ch2_data.append(voltages[2])
                    self.ch3_data.append(voltages[3])
                    
                    self.sample_count += 1
                    
                except Exception as e:
                    print(f"Error in acquisition: {e}")
                    
            # Small sleep to prevent CPU overload (reduce or remove for higher sample rates)
            # time.sleep(0.001)  # Commented out for maximum sample rate
    
    def update_plots(self):
        """Update the plots with new data."""
        if len(self.time_data) > 0:
            # Convert deques to lists for DearPyGui
            time_list = list(self.time_data)
            ch2_list = list(self.ch2_data)
            ch3_list = list(self.ch3_data)
            
            # Update series data
            dpg.set_value("ch2_series", [time_list, ch2_list])
            dpg.set_value("ch3_series", [time_list, ch3_list])
            
            # Update x-axis limits to show latest 10 seconds
            current_time = time_list[-1]
            if current_time > 10:
                x_min = current_time - 10
                x_max = current_time
            else:
                x_min = 0
                x_max = 10
            
            dpg.set_axis_limits("ch2_x_axis", x_min, x_max)
            dpg.set_axis_limits("ch3_x_axis", x_min, x_max)
            
            # Update zero reference lines
            dpg.set_value("ch2_zero_line", [[x_min, x_max], [0, 0]])
            dpg.set_value("ch3_zero_line", [[x_min, x_max], [0, 0]])
            
            # Update status text
            if current_time > 0:
                sample_rate = self.sample_count / current_time
                status = "PAUSED" if self.paused else "RUNNING"
                status_text = f"{status} | Sample Rate: {sample_rate:.1f} Hz | Samples: {self.sample_count} | Time: {current_time:.1f}s"
                dpg.set_value("status_text", status_text)
    
    def start(self):
        """Start the monitor."""
        # Setup GUI
        self.setup_gui()
        
        # Start acquisition thread
        acq_thread = threading.Thread(target=self.acquisition_thread, daemon=True)
        acq_thread.start()
        
        # Main render loop
        while dpg.is_dearpygui_running():
            # Update plots
            self.update_plots()
            
            # Render frame
            dpg.render_dearpygui_frame()
        
        # Cleanup
        self.running = False
        dpg.destroy_context()


def main(sp, node_id):
    """
    Main function to setup and start the monitor.
    
    Args:
        sp: Serial port object
        node_id: Node identifier
    """
   
    print("\n =====================================")
    print(" SUPER-ADC ADS131M04")
    print(" Real-Time Voltage Monitor (DearPyGui)")
    print(" version 2025-11-10 JM")
    print(" =====================================")

    node1 = PIC18F16Q41_JM_ADS131M04_COMMS(node_id, sp)
    daq = PICO2_ADS131M04_DAQ(node1)
    
    print(f"COMMS MCU: {node1.get_version()}")
    print(f"DAQ MCU:   {daq.get_version()}")
    print()
    print("Resetting registers...")
    print(daq.set_clk(8192))  # Set clock to 8192 kHz
    print(daq.set_osr(1024))
    
    # Test a single sample
    print("\nTesting initial sample:")
    voltages = daq.single_sample_as_volts()
    print(f"  CH0: {voltages[0]:+.6f} V")
    print(f"  CH1: {voltages[1]:+.6f} V")
    print(f"  CH2: {voltages[2]:+.6f} V")
    print(f"  CH3: {voltages[3]:+.6f} V")
    
    print("\nStarting real-time plot...")
    print("Close the window or use Ctrl-C to exit.")
    print("\nControls:")
    print("  - Pause/Resume: Pause or resume data acquisition")
    print("  - Reset: Clear all data and restart")
    
    # Create and start the monitor
    monitor = RealtimeVoltageMonitorDPG(daq, max_points=1000)
    monitor.start()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time voltage monitor for ADS131M04 (DearPyGui version)",
        epilog='Close the window or use Ctrl-C to stop.'
    )
    parser.add_argument('-p', '--port', dest='port', default='/dev/ttyUSB0',
                        help='Serial port name (default: /dev/ttyUSB0)')
    parser.add_argument('-i', '--identity', dest='identity', default='C',
                        help='Node identity character (default: C)')
    
    args = parser.parse_args()
    
    sp = rs485.openPort(args.port)
    if sp:
        try:
            main(sp, args.identity)
        except KeyboardInterrupt:
            print("\n\nStopped by user.")
        finally:
            sp.close()
    else:
        print("Could not open serial port.")
    
    print("Done.")
