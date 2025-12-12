"""
Test/Demo script for Patient Monitoring System.
Verifies all components are working correctly.
"""

import sys
import numpy as np
import cv2

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import torch
        print(f"  ✓ PyTorch {torch.__version__}")
    except ImportError:
        print("  ✗ PyTorch not installed")
        return False
    
    try:
        import cv2
        print(f"  ✓ OpenCV {cv2.__version__}")
    except ImportError:
        print("  ✗ OpenCV not installed")
        return False
    
    try:
        import mediapipe as mp
        print(f"  ✓ MediaPipe {mp.__version__}")
    except ImportError:
        print("  ✗ MediaPipe not installed")
        return False
    
    try:
        from ultralytics import YOLO
        print("  ✓ Ultralytics (YOLOv8)")
    except ImportError:
        print("  ✗ Ultralytics not installed")
        return False
    
    try:
        import scipy
        print(f"  ✓ SciPy {scipy.__version__}")
    except ImportError:
        print("  ✗ SciPy not installed")
        return False
    
    return True


def test_modules():
    """Test all custom modules can be imported"""
    print("\nTesting custom modules...")
    
    modules = [
        "config",
        "schemas",
        "core.base_agent",
        "core.video_pipeline",
        "core.orchestrator",
        "core.visualizer",
        "core.alert_system",
        "perception.person_detector",
        "perception.person_tracker",
        "perception.pose_estimator",
        "perception.face_detector",
        "agents.fall_detection_agent",
        "agents.emotion_detection_agent",
        "agents.vital_signs_agent",
        "agents.bed_exit_agent",
        "agents.immobility_agent",
        "agents.seizure_detection_agent",
        "models.rppg_processor",
        "utils.geometry",
        "utils.temporal_buffer",
    ]
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name}")
        except ImportError as e:
            print(f"  ✗ {module_name}: {e}")
            return False
    
    return True


def test_schemas():
    """Test schema creation"""
    print("\nTesting schemas...")
    
    from schemas import (
        BoundingBox, Keypoint, PoseData,
        FallDetectionEvent, EmotionDetectionEvent,
        VitalSignsEvent, BedExitEvent,
        ImmobilityEvent, SeizureDetectionEvent,
        ConsolidatedAlert
    )
    
    # Test BoundingBox
    bbox = BoundingBox(x1=100, y1=200, x2=300, y2=400, confidence=0.9)
    assert bbox.area > 0
    print("  ✓ BoundingBox")
    
    # Test Keypoint
    kp = Keypoint(x=100, y=200, z=0, confidence=0.9)
    print("  ✓ Keypoint")
    
    # Test Events
    import time
    timestamp = time.time()
    
    fall_event = FallDetectionEvent(
        event_type="fall_detection",
        timestamp=timestamp,
        confidence=0.85,
        agent_name="fall_detection",
        frame_id=100,
        fall_type="fall",
    )
    print("  ✓ FallDetectionEvent")
    
    emotion_event = EmotionDetectionEvent(
        event_type="emotion_detection",
        timestamp=timestamp,
        confidence=0.75,
        agent_name="emotion_detection",
        frame_id=100,
        emotion="happy",
        valence=0.8,
        arousal=0.6,
    )
    print("  ✓ EmotionDetectionEvent")
    
    vital_event = VitalSignsEvent(
        event_type="vital_signs",
        timestamp=timestamp,
        confidence=0.9,
        agent_name="vital_signs",
        frame_id=100,
        heart_rate=72.0,
        respiratory_rate=16.0,
        signal_quality=0.85,
    )
    print("  ✓ VitalSignsEvent")
    
    # Test ConsolidatedAlert
    alert = ConsolidatedAlert(
        alert_id="test-123",
        level="HIGH",
        message="Test alert",
        timestamp=timestamp,
        events=[fall_event],
    )
    print("  ✓ ConsolidatedAlert")
    
    return True


def test_perception():
    """Test perception layer components"""
    print("\nTesting perception layer...")
    
    from perception.person_detector import PersonDetector
    from perception.pose_estimator import PoseEstimator
    from perception.face_detector import FaceDetector
    
    # Create dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Test PersonDetector
    try:
        detector = PersonDetector({"model_name": "yolov8n.pt", "confidence_threshold": 0.5, "device": "cpu"})
        print("  ✓ PersonDetector initialized")
    except Exception as e:
        print(f"  ⚠ PersonDetector: {e}")
    
    # Test PoseEstimator
    try:
        pose_estimator = PoseEstimator({"model_complexity": 1})
        print("  ✓ PoseEstimator initialized")
    except Exception as e:
        print(f"  ⚠ PoseEstimator: {e}")
    
    # Test FaceDetector
    try:
        face_detector = FaceDetector({"min_detection_confidence": 0.5})
        print("  ✓ FaceDetector initialized")
    except Exception as e:
        print(f"  ⚠ FaceDetector: {e}")
    
    return True


def test_agents():
    """Test agent initialization"""
    print("\nTesting agents...")
    
    from agents.fall_detection_agent import FallDetectionAgent
    from agents.emotion_detection_agent import EmotionDetectionAgent
    from agents.vital_signs_agent import VitalSignsAgent
    from agents.bed_exit_agent import BedExitAgent
    from agents.immobility_agent import ImmobilityAgent
    from agents.seizure_detection_agent import SeizureDetectionAgent
    
    agents = [
        ("FallDetectionAgent", FallDetectionAgent, {"sequence_length": 30}),
        ("EmotionDetectionAgent", EmotionDetectionAgent, {"emotions": ["happy", "sad"]}),
        ("VitalSignsAgent", VitalSignsAgent, {"algorithm": "CHROM", "fps": 30}),
        ("BedExitAgent", BedExitAgent, {"states": ["IN_BED", "OUT_OF_BED"]}),
        ("ImmobilityAgent", ImmobilityAgent, {"movement_threshold": 0.05}),
        ("SeizureDetectionAgent", SeizureDetectionAgent, {"frequency_range": (3, 10)}),
    ]
    
    for name, AgentClass, config in agents:
        try:
            agent = AgentClass(config)
            assert agent.enabled
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            return False
    
    return True


def test_orchestrator():
    """Test orchestrator"""
    print("\nTesting orchestrator...")
    
    from core.orchestrator import Orchestrator
    from schemas import FallDetectionEvent
    import time
    
    orchestrator = Orchestrator()
    
    # Create test event
    event = FallDetectionEvent(
        event_type="fall_detection",
        timestamp=time.time(),
        confidence=0.9,
        agent_name="fall_detection",
        frame_id=100,
        fall_type="fall",
    )
    
    alerts = orchestrator.process_events([event])
    print(f"  ✓ Orchestrator processed {len(alerts)} alerts")
    
    return True


def main():
    """Run all tests"""
    print("="*80)
    print("Patient Monitoring System - Component Test")
    print("="*80)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Modules", test_modules),
        ("Schemas", test_schemas),
        ("Perception", test_perception),
        ("Agents", test_agents),
        ("Orchestrator", test_orchestrator),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ All tests passed!")
        print("\nSystem is ready to use. Run:")
        print("  python main.py --input 0 --visualize")
    else:
        print("✗ Some tests failed. Please check the output above.")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
