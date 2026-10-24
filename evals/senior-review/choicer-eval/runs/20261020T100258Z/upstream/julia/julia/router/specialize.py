"""Bounds/alias specialization for the validated packed Bend CPU entry point.

Arithmetic and iteration order remain generated from router.bend. This pass is
valid only for bridge.c's distinct packed buffers and checked tile dimensions.
"""
import re


def packed_cpu(source):
    marker = '  WL_CASE(FID_PACKED_DOT)'
    start = source.index(marker)
    stop = source.index('#endif', start)
    body = source[start:stop]
    # Do not generalize this to Array.get: ordinary Bend arrays wrap indices.
    # The bridge pads the full tile ranges and enforces positive bounded sizes.
    specs = {'x': ('const ', 3), 'w': ('const ', 3), 'o': ('', 6)}
    declarations = []
    for name, (qualifier, shift) in specs.items():
        var = f'_{name}_0'
        locs = re.findall(rf'Term (_at_\d+) = blk_loc\(e.mem, {var}\);', body)
        if len(locs) != 1:
            raise RuntimeError(f'Unsupported packed {name} buffer lowering')
        loc = locs[0]
        declarations.append(f'    {qualifier}u32a *restrict julia_{name} = '
                            f'({qualifier}u32a *)(e.mem + blk_loc(e.mem, {var}));')
        body = body.replace(f'Term {loc} = blk_loc(e.mem, {var});', '')
        pattern = rf'blk_at\({var}, (.+), {shift}\)'
        body, count = re.subn(pattern, rf'((u32)(\1) << {shift})', body)
        if count != 1:
            raise RuntimeError(f'Unsupported packed {name} index lowering')
        body = re.sub(rf'blk_read\(e.mem, 0, {loc}, ([^)]+)\)',
                      rf'julia_{name}[\1]', body)
        body = re.sub(rf'blk_write\(e.mem, 0, {loc}, ([^,]+), ([^)]+)\);',
                      rf'julia_{name}[\1] = \2;', body)
    if 'blk_at(' in body or 'blk_read(' in body or 'blk_write(' in body:
        raise RuntimeError('Unrecognized packed buffer access; refusing specialization')
    body = body.replace('    WL_OPEN', '\n'.join(declarations) + '\n    WL_OPEN', 1)
    return source[:start] + body + source[stop:]
