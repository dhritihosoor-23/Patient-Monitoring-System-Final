"""
rPPG (remote photoplethysmography) signal processor.
Extracts heart rate and respiratory rate from facial video using color-based methods.
"""

import numpy as np
from typing import List, Optional, Dict
import cv2
from scipy import signal
from scipy.fft import fft, fftfreq


class RPPGProcessor:
    """
    Remote PPG processor for extracting vital signs from facial video.
    
    Implements CHROM, POS, and ICA algorithms for pulse extraction.
    """
    
    def __init__(self, algorithm: str = "CHROM", fps: float = 30, window_size: int = 300):
        """
        Initialize rPPG processor.
        
        Args:
            algorithm: Algorithm to use ("CHROM", "POS", or "ICA")
            fps: Frame rate
            window_size: Number of frames to process (typically 10 seconds)
        """
        self.algorithm = algorithm
        self.fps = fps
        self.window_size = window_size
        
    def process(self, face_rois: List[np.ndarray]) -> Optional[Dict]:
        """
        Process facial ROIs to extract vital signs.
        
        Args:
            face_rois: List of face crops (RGB images)
            
        Returns:
            Dictionary with heart_rate, respiratory_rate, signal_quality, etc.
            None if processing fails
        """
        if len(face_rois) < self.window_size:
            return None
        
        try:
            # Extract RGB signals
            rgb_signals = self._extract_rgb_signals(face_rois)
            
            if rgb_signals is None:
                return None
            
            # Apply algorithm to extract pulse signal
            if self.algorithm == "CHROM":
                pulse_signal = self._chrom_algorithm(rgb_signals)
            elif self.algorithm == "POS":
                pulse_signal = self._pos_algorithm(rgb_signals)
            else:  # ICA
                pulse_signal = self._ica_algorithm(rgb_signals)
            
            # Extract heart rate from pulse signal
            hr, hr_confidence = self._extract_heart_rate(pulse_signal)
            
            # Extract respiratory rate (simplified)
            rr, rr_confidence = self._extract_respiratory_rate(pulse_signal)
            
            # Compute signal quality
            signal_quality = self._compute_signal_quality(pulse_signal)
            
            return {
                "heart_rate": hr,
                "respiratory_rate": rr,
                "signal_quality": signal_quality,
                "hr_confidence": hr_confidence,
                "rr_confidence": rr_confidence,
            }
            
        except Exception as e:
            print(f"Error in rPPG processing: {e}")
            return None
    
    def _extract_rgb_signals(self, face_rois: List[np.ndarray]) -> Optional[np.ndarray]:
        """Extract mean RGB values from face ROIs"""
        rgb_values = []
        
        for roi in face_rois:
            if roi is None or roi.size == 0:
                continue
            
            # Compute mean RGB values
            mean_rgb = np.mean(roi, axis=(0, 1))
            rgb_values.append(mean_rgb)
        
        if len(rgb_values) < self.window_size:
            return None
        
        return np.array(rgb_values)
    
    def _chrom_algorithm(self, rgb_signals: np.ndarray) -> np.ndarray:
        """
        CHROM (Chrominance-based) algorithm.
        De Haan & Jeanne, "Robust Pulse Rate From Chrominance-Based rPPG", 2013
        """
        # Normalize RGB signals
        rgb_norm = rgb_signals / (np.mean(rgb_signals, axis=0) + 1e-6)
        
        # Chrominance signals
        X = 3 * rgb_norm[:, 0] - 2 * rgb_norm[:, 1]  # R - G
        Y = 1.5 * rgb_norm[:, 0] + rgb_norm[:, 1] - 1.5 * rgb_norm[:, 2]  # R + G - B
        
        # Compute pulse signal
        alpha = np.std(X) / (np.std(Y) + 1e-6)
        pulse = X - alpha * Y
        
        # Bandpass filter (0.7 - 3.0 Hz for HR)
        pulse_filtered = self._bandpass_filter(pulse, 0.7, 3.0)
        
        return pulse_filtered
    
    def _pos_algorithm(self, rgb_signals: np.ndarray) -> np.ndarray:
        """
        POS (Plane-Orthogonal-to-Skin) algorithm.
        Wang et al., "Algorithmic Principles of Remote PPG", 2017
        """
        # Normalize
        rgb_norm = rgb_signals / (np.mean(rgb_signals, axis=0) + 1e-6)
        
        # Projection
        S1 = rgb_norm[:, 1] - rgb_norm[:, 2]  # G - B
        S2 = rgb_norm[:, 1] + rgb_norm[:, 2] - 2 * rgb_norm[:, 0]  # G + B - 2R
        
        # Pulse signal
        h = S1 + (np.std(S1) / (np.std(S2) + 1e-6)) * S2
        
        # Bandpass filter
        pulse_filtered = self._bandpass_filter(h, 0.7, 3.0)
        
        return pulse_filtered
    
    def _ica_algorithm(self, rgb_signals: np.ndarray) -> np.ndarray:
        """
        ICA (Independent Component Analysis) algorithm.
        Simplified version using FastICA-like approach.
        """
        # Normalize
        rgb_norm = rgb_signals / (np.mean(rgb_signals, axis=0) + 1e-6)
        
        # Simple ICA approximation: use green channel (strongest pulse signal)
        pulse = rgb_norm[:, 1]
        
        # Bandpass filter
        pulse_filtered = self._bandpass_filter(pulse, 0.7, 3.0)
        
        return pulse_filtered
    
    def _bandpass_filter(self, signal_data: np.ndarray, low_freq: float, high_freq: float) -> np.ndarray:
        """Apply bandpass filter to signal"""
        nyquist = self.fps / 2
        low = low_freq / nyquist
        high = high_freq / nyquist
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, signal_data)
        
        return filtered
    
    def _extract_heart_rate(self, pulse_signal: np.ndarray) -> tuple:
        """Extract heart rate from pulse signal using FFT"""
        # Perform FFT
        fft_values = fft(pulse_signal)
        fft_freq = fftfreq(len(pulse_signal), 1.0 / self.fps)
        
        # Get positive frequencies
        positive_idx = fft_freq > 0
        fft_freq = fft_freq[positive_idx]
        fft_magnitude = np.abs(fft_values[positive_idx])
        
        # HR range: 40-180 bpm = 0.67-3.0 Hz
        hr_range_mask = (fft_freq >= 0.67) & (fft_freq <= 3.0)
        
        if not np.any(hr_range_mask):
            return 0.0, 0.0
        
        hr_freq = fft_freq[hr_range_mask]
        hr_magnitude = fft_magnitude[hr_range_mask]
        
        # Find peak
        peak_idx = np.argmax(hr_magnitude)
        peak_freq = hr_freq[peak_idx]
        peak_magnitude = hr_magnitude[peak_idx]
        
        # Convert to BPM
        heart_rate = peak_freq * 60
        
        # Confidence based on peak prominence
        confidence = min(1.0, peak_magnitude / (np.mean(hr_magnitude) + 1e-6) / 10)
        
        return heart_rate, confidence
    
    def _extract_respiratory_rate(self, pulse_signal: np.ndarray) -> tuple:
        """
        Extract respiratory rate from pulse signal.
        Simplified: uses low-frequency component.
        """
        # Apply low-pass filter for respiratory component (0.1-0.5 Hz)
        rr_signal = self._bandpass_filter(pulse_signal, 0.1, 0.5)
        
        # Perform FFT
        fft_values = fft(rr_signal)
        fft_freq = fftfreq(len(rr_signal), 1.0 / self.fps)
        
        # Get positive frequencies
        positive_idx = fft_freq > 0
        fft_freq = fft_freq[positive_idx]
        fft_magnitude = np.abs(fft_values[positive_idx])
        
        # RR range: 8-30 breaths/min = 0.13-0.5 Hz
        rr_range_mask = (fft_freq >= 0.13) & (fft_freq <= 0.5)
        
        if not np.any(rr_range_mask):
            return 0.0, 0.0
        
        rr_freq = fft_freq[rr_range_mask]
        rr_magnitude = fft_magnitude[rr_range_mask]
        
        # Find peak
        peak_idx = np.argmax(rr_magnitude)
        peak_freq = rr_freq[peak_idx]
        peak_magnitude = rr_magnitude[peak_idx]
        
        # Convert to breaths per minute
        respiratory_rate = peak_freq * 60
        
        # Confidence
        confidence = min(1.0, peak_magnitude / (np.mean(rr_magnitude) + 1e-6) / 5)
        
        return respiratory_rate, confidence
    
    def _compute_signal_quality(self, pulse_signal: np.ndarray) -> float:
        """Compute signal quality metric"""
        # SNR-based quality metric
        signal_power = np.var(pulse_signal)
        noise_estimate = np.var(np.diff(pulse_signal))  # High-frequency noise
        
        if noise_estimate < 1e-6:
            return 1.0
        
        snr = signal_power / noise_estimate
        quality = min(1.0, snr / 100)
        
        return quality
    
    def reset(self):
        """Reset processor state"""
        pass
