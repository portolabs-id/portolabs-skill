// Person matte for a folder of frames, with Apple Vision through the JavaScript-ObjC bridge
// (macOS 12+, nothing to install or compile).
//
// Usage: osascript -l JavaScript person_matte.js <frames dir> <out dir>
// For every <frames dir>/*.png writes <out dir>/<same name>: white where a person is, at Vision's
// own mask size (ffmpeg scales it back to the frame).
ObjC.import("Foundation");
ObjC.import("AppKit");
ObjC.import("Vision");
ObjC.import("CoreImage");

const ACCURATE = 0;
const ONE_COMPONENT_8 = 1278226488; // kCVPixelFormatType_OneComponent8, 'L008'

function run(argv) {
  if (argv.length !== 2) throw new Error("usage: osascript -l JavaScript person_matte.js <frames dir> <out dir>");
  const [framesDir, outDir] = argv;
  const fm = $.NSFileManager.defaultManager;
  fm.createDirectoryAtPathWithIntermediateDirectoriesAttributesError(outDir, true, $(), null);
  const names = ObjC.deepUnwrap(fm.contentsOfDirectoryAtPathError(framesDir, null))
    .filter((name) => name.endsWith(".png"))
    .sort();
  const request = $.VNGeneratePersonSegmentationRequest.alloc.init;
  request.qualityLevel = ACCURATE;
  request.outputPixelFormat = ONE_COMPONENT_8;
  for (const name of names) {
    const handler = $.VNImageRequestHandler.alloc.initWithURLOptions($.NSURL.fileURLWithPath(`${framesDir}/${name}`), $());
    if (!handler.performRequestsError($([request]), null)) throw new Error(`Vision failed on ${name}`);
    const mask = $.CIImage.imageWithCVPixelBuffer(request.results.objectAtIndex(0).pixelBuffer);
    const png = $.NSBitmapImageRep.alloc.initWithCIImage(mask).representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
    png.writeToFileAtomically(`${outDir}/${name}`, true);
  }
  return `${names.length} mattes`;
}
