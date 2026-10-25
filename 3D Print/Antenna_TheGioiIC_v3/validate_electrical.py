from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent
base_current_min=(3.0-.95)/1050
base_current_max=(3.465-.65)/950
motor_resistance=3/1.68
motor_power=2*1.5**2*motor_resistance
five_volt_current=3+.1+.15
input_power=(5*five_volt_current)/.8+motor_power+3
checks=dict(transistor_base_min_drives_15mA_at_forced_beta10=base_current_min>=.015/10,
            GPIO_base_current_below_8mA=base_current_max<.008,
            five_volt_design_budget_below_module_published_5A=five_volt_current<5,
            adapter_design_budget_below_60W=input_power<60,
            timer_STEP_pulse_us_at_least_5=50>=5,
            encoder_filter_3us_less_than_5ms_edge_interval=3e-6<1/(2400*30/360),
            firmware_build_pass=json.loads((ROOT/'audit/firmware_build_validation.json').read_text())['status']=='PASS_COMPILED_AND_HOST_TESTED')
report=dict(status='PASS_DESIGN_ASSUMPTIONS' if all(checks.values()) else 'FAIL',checks=checks,
    transistor_base_current_min_A=base_current_min,transistor_base_current_max_A=base_current_max,
    estimated_motor_copper_loss_W=motor_power,five_volt_peak_design_current_A=five_volt_current,
    estimated_peak_input_power_W=input_power,adapter_nameplate_W=60,
    actual_hardware_tested=False,
    limitations=['Servo peak3A, encoder0.1A and converter efficiency0.8 are design budgets, not measurements.',
                 'Module current capability, wiring polarity, signal voltages, temperature and pulse timing need bench checks.',
                 'No automatic homing or physical limit switch is included. Manual zero and software limits are explicit.',
                 'Normal software stop retains holding power; physical power isolation is by unplugging the DC adapter.'])
(ROOT/'audit/electrical_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if not all(checks.values()):raise SystemExit(1)
