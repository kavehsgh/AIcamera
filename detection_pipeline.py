import depthai as dai


def setup_detection_pipeline(pipeline, nn_path, label_map):
    nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
    xin_frame = pipeline.create(dai.node.XLinkIn)
    nn_out = pipeline.create(dai.node.XLinkOut)

    xin_frame.setStreamName("inFrame")
    nn_out.setStreamName("nn")

    nn.setConfidenceThreshold(0.5)
    nn.setBlobPath(nn_path)
    nn.setNumInferenceThreads(2)
    nn.input.setBlocking(False)

    xin_frame.out.link(nn.input)
    nn.out.link(nn_out.input)

    return pipeline, xin_frame, nn_out
