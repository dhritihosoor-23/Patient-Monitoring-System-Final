"""
Main application entry point for Patient Monitoring System.
"""

import cv2
import argparse
import sys
from typing import List

from config import (
    VIDEO_CONFIG, PERSON_DETECTION_CONFIG, TRACKING_CONFIG,
    POSE_ESTIMATION_CONFIG, FACE_DETECTION_CONFIG,
    FALL_DETECTION_CONFIG, EMOTION_DETECTION_CONFIG,
    VITAL_SIGNS_CONFIG, BED_EXIT_CONFIG, IMMOBILITY_CONFIG,
    SEIZURE_DETECTION_CONFIG, VISUALIZATION_CONFIG, ALERT_CONFIG
)
from core.video_pipeline import VideoPipeline
from core.orchestrator import Orchestrator
from core.visualizer import Visualizer
from core.alert_system import AlertSystem
from agents.fall_detection_agent import FallDetectionAgent
from agents.emotion_detection_agent import EmotionDetectionAgent
from agents.vital_signs_agent import VitalSignsAgent
from agents.bed_exit_agent import BedExitAgent
from agents.immobility_agent import ImmobilityAgent
from agents.seizure_detection_agent import SeizureDetectionAgent
from schemas import BaseEvent


class PatientMonitoringSystem:
    """
    Main patient monitoring system.
    
    Coordinates all components:
    - Video pipeline
    - Specialized agents
    - Orchestrator
    - Visualization
    - Alerting
    """
    
    def __init__(self, args):
        """Initialize system"""
        self.args = args
        
        # Update video config from args
        video_config = VIDEO_CONFIG.copy()
        video_config["input_source"] = args.input
        
        # Initialize components
        print("\n" + "="*80)
        print("Patient Monitoring System - Initializing")
        print("="*80 + "\n")
        
        self.video_pipeline = VideoPipeline(video_config)
        self.orchestrator = Orchestrator()
        self.visualizer = Visualizer(VISUALIZATION_CONFIG)
        self.alert_system = AlertSystem(ALERT_CONFIG)
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Output video writer
        self.video_writer = None
        if args.output:
            self._init_video_writer(args.output, video_config)
        
        print("\n" + "="*80)
        print("Initialization Complete")
        print("="*80 + "\n")
    
    def _initialize_agents(self) -> List:
        """Initialize all monitoring agents"""
        agents = []
        
        print("Initializing agents...")
        
        # Fall detection
        agents.append(FallDetectionAgent(FALL_DETECTION_CONFIG))
        print("  ✓ Fall Detection Agent")
        
        # Emotion detection
        agents.append(EmotionDetectionAgent(EMOTION_DETECTION_CONFIG))
        print("  ✓ Emotion Detection Agent")
        
        # Vital signs
        agents.append(VitalSignsAgent(VITAL_SIGNS_CONFIG))
        print("  ✓ Vital Signs Agent")
        
        # Bed exit
        agents.append(BedExitAgent(BED_EXIT_CONFIG))
        print("  ✓ Bed Exit Agent")
        
        # Immobility
        agents.append(ImmobilityAgent(IMMOBILITY_CONFIG))
        print("  ✓ Immobility Agent")
        
        # Seizure detection
        agents.append(SeizureDetectionAgent(SEIZURE_DETECTION_CONFIG))
        print("  ✓ Seizure Detection Agent")
        
        return agents
    
    def _init_video_writer(self, output_path: str, video_config: dict):
        """Initialize video writer for output"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = video_config.get("fps", 30)
        width = video_config.get("frame_width", 1280)
        height = video_config.get("frame_height", 720)
        
        self.video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        print(f"  ✓ Video output: {output_path}")
    
    def run(self):
        """Main processing loop"""
        # Initialize video pipeline
        self.video_pipeline.initialize(
            PERSON_DETECTION_CONFIG,
            TRACKING_CONFIG,
            POSE_ESTIMATION_CONFIG,
            FACE_DETECTION_CONFIG
        )
        
        if not self.video_pipeline.start():
            print("Error: Could not start video pipeline")
            return
        
        print("\nStarting monitoring...")
        print("Press 'q' to quit\n")
        
        try:
            while True:
                # Read frame
                frame, metadata = self.video_pipeline.read_frame()
                
                if frame is None:
                    print("End of video stream")
                    break
                
                # Process with all agents
                events = []
                for agent in self.agents:
                    event = agent.detect(frame, metadata)
                    if event:
                        events.append(event)
                
                # Orchestrate events
                alerts = self.orchestrator.process_events(events)
                
                # Send alerts
                if alerts:
                    self.alert_system.send_alerts(alerts)
                
                # Get latest vital signs for display
                vital_signs = self._get_latest_vital_signs(events)
                
                # Visualize
                if self.args.visualize:
                    vis_frame = self.visualizer.render(frame, metadata, alerts, vital_signs)
                    
                    # Display
                    cv2.imshow("Patient Monitoring System", vis_frame)
                    
                    # Write to output video
                    if self.video_writer:
                        self.video_writer.write(vis_frame)
                    
                    # Check for quit
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nStopping...")
                        break
                else:
                    # Write original frame to output
                    if self.video_writer:
                        self.video_writer.write(frame)
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            self.cleanup()
    
    def _get_latest_vital_signs(self, events: List[BaseEvent]) -> dict:
        """Extract latest vital signs from events"""
        for event in reversed(events):
            if event.event_type == "vital_signs":
                return {
                    "heart_rate": event.heart_rate,
                    "respiratory_rate": event.respiratory_rate,
                    "signal_quality": event.signal_quality,
                }
        return {}
    
    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        
        self.video_pipeline.stop()
        
        if self.video_writer:
            self.video_writer.release()
        
        cv2.destroyAllWindows()
        
        print("✓ Cleanup complete")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Patient Monitoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with webcam
  python main.py --input 0 --visualize
  
  # Run with video file
  python main.py --input video.mp4 --visualize --output output.mp4
  
  # Run without visualization (headless)
  python main.py --input video.mp4 --output output.mp4
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default="0",
        help="Input video source (0 for webcam, or path to video file)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output video path (optional)"
    )
    
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Show real-time visualization"
    )
    
    args = parser.parse_args()
    
    # Convert input to int if it's a number (webcam index)
    try:
        args.input = int(args.input)
    except ValueError:
        pass  # It's a file path
    
    # Create and run system
    system = PatientMonitoringSystem(args)
    system.run()


if __name__ == "__main__":
    main()
