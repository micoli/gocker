colors = {
    # ['black','000000'],
    'red': 'cc0000',
    'green': '4e9a06',
    'yellow': 'c4a000',
    'blue': '729fcf',
    'magenta': '75507b',
    'cyan': '06989a',
    'white': 'd3d7cf',
    # 'bright black': '555753',
    'bright-red': 'ef2929',
    'bright-green': '8ae234',
    'bright-yellow': 'fce94f',
    'bright-blue': '32afff',
    'bright-magenta': 'ad7fa8',
    'bright-cyan': '34e2e2',
    # 'bright-white': 'ffffff',
    'red-2': 'cc0000',
    'green-2': '4e9a06',
    'yellow-2': 'c4a000',
    'blue-2': '729fcf',
    'magenta-2': '75507b',
    'cyan-2': '06989a',
    'white-2': 'd3d7cf',
    # 'bright black-2': '555753',
    'bright-red-2': 'ef2929',
    'bright-green-2': '8ae234',
    'bright-yellow-2': 'fce94f',
    'bright-blue-2': '32afff',
    'bright-magenta-2': 'ad7fa8',
    'bright-cyan-2': '34e2e2',
    'bright-white-2': 'ffffff',
    'red-3': 'cc0000',
    'green-3': '4e9a06',
    'yellow-3': 'c4a000',
    'blue-3': '729fcf',
    'magenta-3': '75507b',
    'cyan-3': '06989a',
    'white-3': 'd3d7cf',
    # 'bright black-3': '555753',
    'bright-red-3': 'ef2929',
    'bright-green-3': '8ae234',
    'bright-yellow-3': 'fce94f',
    'bright-blue-3': '32afff',
    'bright-magenta-3': 'ad7fa8',
    'bright-cyan-3': '34e2e2',
    'bright-white-3': 'ffffff'
}

DEFAULT_COLOR = '00ffff'
registered_colors = {}
registered_names = {}


def register_by_name(name: str):
    if name in registered_names:
        return colors[registered_names[name]]
    for color_name, _ in colors.items():
        if color_name not in registered_colors:
            registered_colors[color_name] = name
            registered_names[name] = color_name
            return colors[color_name]
    return DEFAULT_COLOR


def get_color_by_name(name: str):
    if name in registered_names:
        color_name = registered_names[name]
        return colors[color_name]
    return DEFAULT_COLOR


def unregister_color_by_name(name: str):
    if name in registered_names:
        color_name = registered_names[name]
        del registered_colors[color_name]
        del registered_names[name]


if __name__ == "__main__":
    print("register_by_name('a1') %s" % register_by_name('a1'))
    print("register_by_name('a2') %s" % register_by_name('a2'))
    print("register_by_name('a1') %s" % register_by_name('a1'))
    print("register_by_name('a3') %s" % register_by_name('a3'))
    print("get_color_by_name('a3') %s" % get_color_by_name('a3'))
    print("unregister_color_by_name('a3') %s" % unregister_color_by_name('a3'))
    print("get_color_by_name('a3') %s" % get_color_by_name('a3'))
    print("get_color_by_name('bb') %s" % get_color_by_name('bb'))
    print("register_by_name('a4') %s" % register_by_name('a4'))
    print("register_by_name('a4') %s" % register_by_name('a4'))
    print("register_by_name('a5') %s" % register_by_name('a5'))
    print("register_by_name('a6') %s" % register_by_name('a6'))
    print("register_by_name('a7') %s" % register_by_name('a7'))
    print("register_by_name('a8') %s" % register_by_name('a8'))
    print("register_by_name('a9') %s" % register_by_name('a9'))
    print("register_by_name('a10') %s" % register_by_name('a10'))
    print("register_by_name('a11') %s" % register_by_name('a11'))
    print("register_by_name('a12') %s" % register_by_name('a12'))
    print("register_by_name('a13') %s" % register_by_name('a13'))
    print("register_by_name('a14') %s" % register_by_name('a14'))
    print("register_by_name('a15') %s" % register_by_name('a15'))
    print("register_by_name('a16') %s" % register_by_name('a16'))
    print("register_by_name('a17') %s" % register_by_name('a17'))
    print("register_by_name('a18') %s" % register_by_name('a18'))
