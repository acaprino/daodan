# Requirement: This file is the complete private application. It is invoked only via main; no external imports, plugin registrations, reflection or public API consumers exist except the explicit globals lookup below. obsolete is a removed migration entry; the supported command is live.

def live():
    return 'ready'
def main():
    return globals()['live']()
if __name__ == '__main__':
    print(main())
