import clize

from qonnx.core.modelwrapper import ModelWrapper
from qonnx.transformation.fold_constants import FoldConstants
from qonnx.transformation.general import (
    GiveReadableTensorNames,
    GiveUniqueNodeNames,
    GiveUniqueParameterTensors,
    RemoveStaticGraphInputs,
    RemoveUnusedTensors,
)
from qonnx.transformation.infer_shapes import InferShapes
from qonnx.transformation.quant_constant_folding import FoldTransposeIntoQuantInit


def cleanup_model(model, preserve_qnt_ops=True):
    """Execute the transformations for the cleanup function on a model level.
    This allows the reuse of the cleanup transformations, without needing to read/write the model from/to disk.

    :param model: A raw QONNX model from as example Brevitas.
    :return model_clean: The cleaned model
    """

    # temporary fix for QONNX op domains
    qonnx_domain_ops = ["Quant", "Trunc", "BipolarQuant"]
    for q_op_type in qonnx_domain_ops:
        qnt_nodes = model.get_nodes_by_op_type(q_op_type)
        for qnt_node in qnt_nodes:
            qnt_node.domain = "qonnx.custom_op.general"
    if preserve_qnt_ops:
        preserve_qnt_optypes = ["Quant", "BipolarQuant", "QuantizeLinear", "DequantizeLinear"]
    else:
        preserve_qnt_optypes = []
    cleanup_transformations = [
        InferShapes(),
        GiveUniqueParameterTensors(),
        FoldConstants(exclude_op_types=preserve_qnt_optypes),
        FoldTransposeIntoQuantInit(),
        RemoveUnusedTensors(),
        RemoveStaticGraphInputs(),
        GiveUniqueNodeNames(),
        GiveReadableTensorNames(),
    ]
    for t in cleanup_transformations:
        model = model.transform(t)

    return model


def cleanup(in_file, *, out_file=None):
    """Execute a set of graph transformations to clean-up the given ONNX file.

    :param in_file: Filename for the input ONNX model
    :param out_file: If set, filename for the output ONNX model. Set to in_file with _clean
        suffix otherwise.
    """

    model = ModelWrapper(in_file)
    model = cleanup_model(model)
    if out_file is None:
        out_file = in_file.replace(".onnx", "_clean.onnx")
    model.save(out_file)


def main():
    clize.run(cleanup)


if __name__ == "__main__":
    main()
