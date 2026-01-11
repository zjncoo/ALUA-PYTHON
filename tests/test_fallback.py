
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import process_data

def test_dead_sensors_fallback():
    print("Testing One: All Sensors Dead")
    # Create dead data (below threshold 10)
    dead_data = []
    for i in range(100):
        dead_data.append({
            "TIMESTAMP": i * 0.1,
            "SCL0": 5.0, # Dead
            "SCL1": 5.0, # Dead
            "SLIDER0": 500,
            "SLIDER1": 500,
            "RELAZIONI_P0": ["AMICALE"],
            "RELAZIONI_P1": ["AMICALE"]
        })
    
    # Run process
    result = process_data.processa_dati(dead_data)
    
    # Check fallback trigger
    fallback = result.get("fallback_scenario")
    print(f"Fallback Scenario Triggered: {fallback}")
    
    if fallback in ["NO-NO", "YES-YES", "NO-YES", "YES-NO"]:
        print("✅ Fallback Scenario selection valid.")
    else:
        print("❌ Fallback Scenario NOT triggering or invalid.")
        return

    # Check arousal dict consistency
    arousal = result.get("elaborati", {}).get("arousal", {})
    p0_state = arousal["persona0"]["arousal"]
    p1_state = arousal["persona1"]["arousal"]
    
    # Validate against scenario string "NO-YES" -> False, True
    expected_s0 = (fallback.split("-")[0] == "YES")
    expected_s1 = (fallback.split("-")[1] == "YES")
    
    if p0_state == expected_s0 and p1_state == expected_s1:
         print(f"✅ Arousal Dict consistent with scenario: P0={p0_state}, P1={p1_state}")
    else:
         print(f"❌ Inconsistency! Scenario={fallback} vs Dict P0={p0_state}/P1={p1_state}")

    # Test Asset Gen dry run
    print("Testing Asset Generation (Fake Data Injection)...")
    try:
        assets = process_data.processa_e_genera_assets(dead_data, result, output_dir="/tmp/alua_test_output")
        if "qr_code" in assets:
             print("✅ Assets generated successfully (QR code present).")
             print(f"QR Link: {assets.get('qr_link')}")
        else:
             print("❌ QR code missing in assets.")
    except Exception as e:
        print(f"❌ Asset generation failed: {e}")

if __name__ == "__main__":
    test_dead_sensors_fallback()
