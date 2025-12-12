import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from contract_blocks import conductance_graph

print("Testing conductance graph generation...")
output = conductance_graph.genera_grafico_conduttanza([], "test_conductance.png")
print(f"Output path: {output}")

if os.path.exists(output):
    print("SUCCESS: File generated.")
    # Verify size? Not easily in python without PIL, but ls -l will show size
else:
    print("FAILURE: File not generated.")
