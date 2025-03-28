import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import transforms
from matplotlib.animation import FuncAnimation
from tls_client import TLSClient

class ArtificialHorizon:
    def __init__(self, server_address="192.168.10.168", server_port=12347, small_threshold=2):
        self.small_threshold = small_threshold

        # Sensor server configuration and connection.
        self.client = TLSClient(server_address, server_port)
        self.client.connect()

        # Integrated angle estimates.
        self.pitch_est = 0.0  # Approximate pitch angle (degrees)
        self.roll_est = 0.0   # Approximate roll angle (degrees)
        
        # Record the initial time for dt computation.
        self.last_time = time.time()
        
        # Set up the matplotlib figure and axis.
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.axis("off")  # Hide the axes for a clean look
        
        # Define coordinates for the sky and ground patches.
        sky_coords = [(-2, 0), (2, 0), (2, 2), (-2, 2)]
        ground_coords = [(-2, -2), (2, -2), (2, 0), (-2, 0)]
        
        # Create polygon patches for the sky and ground.
        self.sky_patch = patches.Polygon(sky_coords, closed=True, facecolor="skyblue", edgecolor="none")
        self.ground_patch = patches.Polygon(ground_coords, closed=True, facecolor="sienna", edgecolor="none")
        self.ax.add_patch(self.sky_patch)
        self.ax.add_patch(self.ground_patch)
        
        # Text annotations to display the current estimated angles.
        self.pitch_text = self.ax.text(-0.95, 0.90, '', transform=self.ax.transAxes, fontsize=12, color="white")
        self.roll_text = self.ax.text(-0.95, 0.82, '', transform=self.ax.transAxes, fontsize=12, color="white")
        self.yaw_text = self.ax.text(-0.95, 0.74, '', transform=self.ax.transAxes, fontsize=12, color="white")
        
        # Scaling factor to translate pitch into vertical movement.
        self.pitch_scale = 0.01  # Adjust as needed
        
        # Set up the animation.
        self.ani = FuncAnimation(self.fig, self.update, interval=100, blit=True)
    
    def get_sensor_rates(self):
        """
        Reads sensor values assumed to be angular velocities in degrees per second.
        Returns:
          - x_rate: angular velocity for pitch (nose up/down)
          - y_rate: angular velocity for roll (wing tilt)
          - z_rate: angular velocity for yaw (not integrated)
        """
        x_rate = self.client.send_read_request("x_angle").get('value')
        y_rate = self.client.send_read_request("y_angle").get('value')
        z_rate = self.client.send_read_request("z_angle").get('value')
        return (
            x_rate if abs(x_rate) > self.small_threshold else 0,
            y_rate if abs(y_rate) > self.small_threshold else 0,
            z_rate if abs(z_rate) > self.small_threshold else 0
        )
    
    def update(self, frame):
        # Compute elapsed time (dt) since the last update.
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Get the angular velocity readings from the sensor.
        pitch_rate, roll_rate, yaw_rate = self.get_sensor_rates()
        
        # Integrate the angular velocities to update the estimated angles.
        self.pitch_est += pitch_rate * dt
        self.roll_est += roll_rate * dt
        
        # Create an affine transformation:
        # - Rotate the horizon by the integrated roll angle.
        # - Translate vertically according to the integrated pitch (scaled).
        trans = transforms.Affine2D().rotate_deg(self.roll_est).translate(0, self.pitch_est * self.pitch_scale)
        
        # Apply the transformation to both sky and ground patches.
        self.sky_patch.set_transform(trans + self.ax.transData)
        self.ground_patch.set_transform(trans + self.ax.transData)
        
        # Update the displayed angle values.
        self.pitch_text.set_text(f"Pitch Angle: {self.pitch_est:.2f}°")
        self.roll_text.set_text(f"Roll Angle: {self.roll_est:.2f}°")
        self.yaw_text.set_text(f"Yaw Rate: {yaw_rate:.2f}°/s")
        
        return self.sky_patch, self.ground_patch, self.pitch_text, self.roll_text, self.yaw_text
    
    def start(self):
        """Starts the artificial horizon display."""
        plt.show()


if __name__ == "__main__":
    horizon = ArtificialHorizon()
    horizon.start()