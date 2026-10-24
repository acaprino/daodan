# Python 3.13. Contract: omitted output creates a new independent collection each call; explicitly supplied output is appended in place.
def collect(item, output=None):
    if output is None: output = []
    output.append(item)
    return output
