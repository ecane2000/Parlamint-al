
import sys
import os

# Add current directory to path so we can import src as a package
sys.path.append(os.getcwd())

from src.segment import _reinsert_breaks_before_cues
from src.utils import reconstructing_broken_lines_helper # We will test the helper directly first if possible, or via segment

# But wait, I haven't implemented it yet. 
# Ideally I should verify the full pipeline via segment_by_speakers or just test the helper.
# I'll stick to testing the helper logic basically, but since it's not exported yet I'll mock it or import it once created.
# Actually, let's keep the script simple and just test the splitting function, 
# BUT the splitting function relies on the input ALREADY being reconstructed.
# The user wants "reconstruct broken lines" to happen BEFORE splitting.
# So I should test the reconstruction function separately or test the composition.

# Let's write the test for the utility function primarily, as that's the core logic change.
# I will assume the function name is reconstruct_broken_lines.

def test_reconstruction():
    from src.utils import reconstruct_broken_lines # Will exist soon
    
    print("\nRunning Line Reconstruction Tests...\n")
    
    test_cases = [
        {
            "name": "Broken line merge",
            "input": "This is a broken\nline.",
            "expected": "This is a broken line."
        },
        {
            "name": "Sentence split preserved",
            "input": "First sentence.\nSecond sentence.",
            "expected": "First sentence.\nSecond sentence."
        },
        {
            "name": "Question mark split preserved",
            "input": "Really?\nYes.",
            "expected": "Really?\nYes."
        },
        {
            "name": "Exclamation mark split preserved",
            "input": "Wow!\nIndeed.",
            "expected": "Wow!\nIndeed."
        },
        {
            "name": "Speaker cue lost merge (Intended)",
            "input": "He was saying\nName Surname - checks out.",
            "expected": "He was saying Name Surname - checks out."
        },
        {
            "name": "Speaker cue preserved split",
            "input": "He said.\nName Surname - starts new.",
            "expected": "He said.\nName Surname - starts new."
        }
    ]
    
    failures = 0
    for case in test_cases:
        print(f"Test: {case['name']}")
        output = reconstruct_broken_lines(case['input'])
        
        # Check equality
        # Note: reconstruct_broken_lines might handle newlines etc differently?
        # Expectation: it returns a string with fewer newlines.
        
        if output.strip() == case['expected'].strip():
            print(f"PASS")
        else:
            print(f"FAIL")
            print(f"  Input:    {repr(case['input'])}")
            print(f"  Expected: {repr(case['expected'])}")
            print(f"  Got:      {repr(output)}")
            failures += 1
        print("-" * 30)
        
    if failures == 0:
        print("\nALL RECONSTRUCTION TESTS PASSED")
    else:
        print(f"\n{failures} TESTS FAILED")

if __name__ == "__main__":
    try:
        test_reconstruction()
    except ImportError:
        print("ImportError: Could not import reconstruct_broken_lines. Implement it first.")
    except Exception as e:
        print(f"An error occurred: {e}")
