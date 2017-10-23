def hex2rgb(hex):
    return tuple(int(hex.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))

def rgb2hex(r,g,b):
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex

