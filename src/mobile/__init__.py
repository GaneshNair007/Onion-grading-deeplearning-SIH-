"""Phone-only mobile integration core (framework-neutral).

The current app framework is a FastAPI backend (backend/app/main.py) serving
a web/mobile client — there is no native Android/Flutter/React Native layer
in this repository yet. Per the project rules, the browser is treated as a
documented mobile integration boundary: real phone speaker/mic capture must
come from a native app that calls these functions (or the FastAPI endpoints),
not from browser microphone APIs.

Required app functions (native side):
    scanOnionImage(image)            -> backend /api/scan/vision
    recordAmbientBaseline()          -> src.mobile.capture_protocol.begin_session
    runPhoneAcousticTest()           -> src.mobile.capture_protocol.measure_onion
    classifyVision(image)            -> inference/vision_inference.classify_vision
    classifyAcoustic(audio)          -> inference/acoustic_inference.classify_acoustic
    fuseResults(vision, acoustic)    -> src.fusion.fuse_results
    saveScanResult(result)           -> backend /api/scan/fuse

Each inference module is independently testable and does not import the app
framework.
"""
