
def getStylesheet(name):
    if name == "orange":
        f = open("orange.sheet", "r")
        sheet = ""
        line = " "
        while line:
            sheet += line
            line = f.readline()
        f.close()
        return sheet

if __name__ == '__main__':
    getStylesheet("orange")