import os, util

#REQUIRE['imagemagick'] = ['convert']

def imagemagick(icon, target, size, fmt):
    if os.path.exists(icon):
        util.mkdir(os.path.dirname(target))
        util.command(['convert',icon,
            '-filter','Cubic',
            '-resize',str(size)+"x"+str(size),
                target+'.'+fmt])
    else:
        util.error("Icon does not exist:",os.path.join(os.getcwd(),icon))
