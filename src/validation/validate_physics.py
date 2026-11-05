import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from simulation.physics_model import (CarParams, TrackParams, run_lap, grip_window,
                                      mu_effective, build_track, RHO_AIR)

def test_grip_window_peak():
    cp = CarParams()
    fT_peak = grip_window(cp.T_opt, cp)
    assert abs(fT_peak - 1.0) < 1e-10, 'Gaussian grip window peak must be 1.0 at T_opt'
    print('PASS: grip_window peak = 1.0 at T_opt')

def test_grip_window_falloff():
    cp = CarParams()
    fT_cold = grip_window(cp.T_opt - 2*cp.sigma_T, cp)
    assert fT_cold < 0.15, 'Grip must fall significantly outside 2-sigma window'
    print('PASS: grip_window falloff outside 2-sigma: %.4f' % fT_cold)

def test_traction_ceiling_positive():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    assert (res['F_trac_max'] > 0).all(), 'Traction ceiling must be positive everywhere'
    print('PASS: F_trac_max > 0 everywhere')

def test_soc_bounds():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    assert res['SOC'].min() >= 0.19, 'SOC must not fall below lower bound'
    assert res['SOC'].max() <= 0.96, 'SOC must not exceed upper bound'
    print('PASS: SOC bounds respected [%.3f, %.3f]' % (res['SOC'].min(), res['SOC'].max()))

def test_tyre_temp_bounds():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    assert res['T_tire'].min() >= 39.0, 'Tyre temp must not fall below 40C floor'
    assert res['T_tire'].max() <= 151.0, 'Tyre temp must not exceed 150C ceiling'
    print('PASS: T_tire bounds respected [%.1fC, %.1fC]' % (res['T_tire'].min(), res['T_tire'].max()))

def test_velocity_positive():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    assert (res['v'] > 0).all(), 'Velocity must remain positive throughout lap'
    print('PASS: v > 0 throughout lap')

def test_wear_monotonic():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    diff = np.diff(res['wear'])
    assert (diff >= -1e-8).all(), 'Tyre wear must be monotonically non-decreasing'
    print('PASS: tyre wear monotonically non-decreasing')

def test_lap_time_physical():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    lt = res['lap_time']
    # Floor: the whole lap at the power-limited top speed, P = 0.5 rho Cd A v^3
    P_max = cp.eta_dt * (cp.P_ICE_max + 0.55 * cp.P_MGUK_max)
    v_top = (P_max / (0.5 * RHO_AIR * cp.Cd_X * cp.A_ref)) ** (1.0 / 3.0)
    floor = tp.L / v_top
    assert floor < lt < 150.0, 'Lap time %.2f s outside physical range [%.1f, 150] s' % (lt, floor)
    print('PASS: lap time physical: %.2f s' % lt)

def test_energy_conservation():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    # dSOC/dt = -P_bat / E_bat at every node the SOC clip does not touch
    expected = -(res['P_MGUK_kW'][:-1] * 1e3 / cp.E_bat) * res['dt'][:-1]
    free = (res['SOC'][1:] > 0.20) & (res['SOC'][1:] < 0.95)
    assert free.any() and np.allclose(np.diff(res['SOC'])[free], expected[free], rtol=0, atol=1e-12),         'SOC change must equal battery energy flow'
    print('PASS: SOC balance holds at %d nodes' % free.sum())

def test_corner_widths_and_amplitudes_independent():
    track = build_track(TrackParams())
    r = np.corrcoef(track['corner_widths'], track['corner_amps'])[0, 1]
    assert abs(r) < 0.99, 'Corner widths and amplitudes must be independent draws'
    print('PASS: corner width/amplitude correlation = %.3f' % r)

def test_traction_ceiling_uses_total_normal_load():
    cp = CarParams(); tp = TrackParams()
    res = run_lap(cp, tp)
    normal_load = res['F_trac_max'] / res['mu_eff']
    # Coulomb limit: N = m g + F_down, with m g = 768 * 9.81 = 7534.08 N
    assert np.allclose(normal_load - res['F_down'], 7534.08, rtol=1e-9), \
        'Normal load must be weight plus downforce'
    print('PASS: F_trac_max = mu_eff * (7534.08 N + F_down)')

def test_track_is_closed():
    tp = TrackParams()
    track = build_track(tp)
    net_turn = np.sum(track['kappa']) * track['ds']
    assert abs(net_turn - 2 * np.pi) < 1e-9, 'A closed circuit turns exactly once'
    gap = np.hypot(track['x'][-1], track['y'][-1])
    assert gap < 1e-6, 'Track must end where it starts (x = y = 0)'
    print('PASS: net turn = 2 pi, end gap = %.1e m' % gap)

def test_mu_effective_matches_published_equation():
    # mu0 (1 - 1e4 k_w w) at T_opt: 1.75 * (1 - 1e4 * 2e-6 * 0.5) = 1.7325
    assert abs(mu_effective(95.0, 0.5, CarParams()) - 1.7325) < 1e-12,         'mu_eff must match the README equation'
    print('PASS: mu_eff matches the published equation')

def run_all():
    tests = [
        test_grip_window_peak,
        test_grip_window_falloff,
        test_traction_ceiling_positive,
        test_soc_bounds,
        test_tyre_temp_bounds,
        test_velocity_positive,
        test_wear_monotonic,
        test_lap_time_physical,
        test_energy_conservation,
        test_corner_widths_and_amplitudes_independent,
        test_traction_ceiling_uses_total_normal_load,
        test_track_is_closed,
        test_mu_effective_matches_published_equation,
    ]
    passed = 0; failed = 0
    for t in tests:
        try:
            t(); passed += 1
        except AssertionError as e:
            print('FAIL: ' + str(e)); failed += 1
        except Exception as e:
            print('ERROR: ' + str(e)); failed += 1
    print('\nValidation complete: %d passed  %d failed' % (passed, failed))
    return failed == 0

if __name__ == '__main__':
    ok = run_all()
    sys.exit(0 if ok else 1)
