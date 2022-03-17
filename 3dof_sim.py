# Change Log
#Added pid loop for pitch needs tuning and variable gains
#Kinda getting somwhere maybe?

from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt



def dragModel(x, Cd=0.1):
    # Input: state vector x
    # Returns: drag force given current velocity vector and attitude
    #
    # Probably want to add the previous thrust command in here as well
    # Honestly not sure what the prop dynamics look like.
    # Drag is low when cross section is low, drag is high when cross section is high??

    x_dot = x[2]
    y_dot = x[3]
    theta = x[4]
    airspeed = np.sqrt(x_dot ** 2 + y_dot ** 2)
    airspeed_angle = np.arctan2(y_dot, x_dot)
    return -1 * Cd * np.abs(np.sin(theta - airspeed_angle)) * airspeed * np.array([x_dot, y_dot])

def stateDerivative(state_vector,input_vector,g=9.8055):
    [x,y,x_dot,y_dot,theta,theta_dot] = state_vector
    [F,M] = input_vector #Force in the body and moment about cg
    theta_ddot = M / 0.00939 #M/I
    [Fdx, Fdy] = dragModel(state_vector)
    x_ddot = F*np.sin(theta)/0.82 + Fdx #Acceleration = Force/Mass
    y_ddot = F*np.cos(theta)/0.82 + Fdy - g
    return np.array([x_dot,y_dot,x_ddot,y_ddot,theta_dot,theta_ddot])

def thrust(pwm):
    pwm_percent = (pwm-1000)/1000
    max_motor_thrust = (470*2)/1000*kg2n #kilo/grams
    return pwm_percent*max_motor_thrust

# 4th Order Runge Kutta Calculation
def RK4(x,u,dt):
    # Inputs: x[k], u[k], dt (time step, seconds)
    # Returns: x[k+1]
    # Calculate slope estimates
    K1 = stateDerivative(x, u)
    K2 = stateDerivative(x + K1 * dt / 2, u)
    K3 = stateDerivative(x + K2 * dt / 2, u)
    K4 = stateDerivative(x + K3 * dt, u)
    # Calculate x[k+1] estimate using combination of slope estimates
    x_next = x + (1/6 * (K1+ 2*K2 + 2*K3 + K4) * dt)
    return np.array(x_next)

def allocate_thrust(u):
    # Inputs: u[k]
    # Returns allocation PWM values for a given force/torque command
    # Right now this just returns the input vector u because I haven't changed the controller to output [Fx, Fy, T].
    return u



#######
# Magic Numbers
in2m = 0.0254
kg2n= 9.8055

# Vehicle Properties
arm_length = 5 *in2m

# Integration options
dt=1/1500
tf = 10
sim_t = np.arange(0,tf,dt)

#Inital State
state_itt = np.zeros((len(sim_t),9))
state = [0,0,0,0,0,0]

#Control
kp_alt = 10
ki_alt = 3
kd_alt = 0
alt_i = 0
prev_alt_i = 0
prev_alt_error =0
alt_output =1000

kp_pitch = 0.25
ki_pitch = 0.001
kd_pitch = 0.1
pitch_i = 0
prev_pitch_i = 0
prev_pitch_error =0
pitch_output=1000


control_timer =0
control_dt = 1/250

# Actuators
pwm_input = 1000

#Noise
alt_noise = 0
pitch_noise =0



for i in range (0,len(sim_t)):
    #do a bunch of random voodo
    #get the hoodo
    #sim results

    if sim_t[i]-control_timer >= control_dt:
        control_timer = sim_t[i]
        #alltitude pid

        alt_error = 0-state[1] + alt_noise
        alt_p = kp_alt*alt_error
        alt_i = prev_alt_i + (ki_alt*alt_error*control_dt)
        prev_alt_i = alt_i
        alt_d = kd_alt*(prev_alt_error - alt_error)/control_dt
        prev_alt_error = alt_error
        alt_output = alt_p+alt_i+alt_d+1436.31415926

        #pitch pid
        pitch_error =  state[4]-0
        pitch_p = kp_pitch * pitch_error
        pitch_i = prev_pitch_i + (ki_pitch * pitch_error * control_dt)
        prev_pitch_i = pitch_i
        pitch_d = kd_pitch * (prev_pitch_error - pitch_error) / control_dt
        prev_alt_error = pitch_error
        pitch_output = pitch_p + pitch_i + pitch_d






    m1_force = thrust(alt_output+pitch_output)
    m2_force = thrust(alt_output-pitch_output)
    M = m1_force*arm_length - m2_force*arm_length

    if i>0:
        state = state_itt[i-1][:]
    else:
        alt_error =0


    state_itt[i][0:6] = RK4(np.array(state[0:6]),np.array([m1_force+m2_force,M]),dt)
    state_itt[i][6] = alt_error
    state_itt[i][7] = alt_i
    state_itt[i][8] = alt_output


plt.subplots(3, 1)

plt.subplot(3, 1, 1)
plt.plot(sim_t, state_itt[:,6], 'r--', label="altitude_output")
plt.legend()
plt.xlabel('Y Position (m)')
plt.ylabel('Pid Output')

plt.subplot(3, 1, 2)
plt.plot(sim_t, state_itt[:,0], 'r--', label="x_pos")
plt.plot(sim_t, state_itt[:,1], 'k--', label="y_pos")
plt.legend()
plt.xlabel('Time(s)')
plt.ylabel('Pos(m) ')

plt.subplot(3, 1, 3)
plt.plot(sim_t, state_itt[:,2], 'r--', label="x_dot")
plt.plot(sim_t, state_itt[:,3], 'k--', label="y_dot")
plt.legend()
plt.xlabel('Time(s)')
plt.ylabel('Velocity(m/s)')

plt.show()
