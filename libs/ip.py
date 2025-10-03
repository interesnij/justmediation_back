class IPList(list):
    """ Разрешить сетевые маски в настройках INTERNAL_IPS.
    Аргументы:
        ips (список): Список IP-адресов или масок в виде строк
    Использование:
        INTERNAL_IPS = IPList(['127.0.0.1', '192.168.1.0/24'])
    """

    def __init__(self, ips):
        try:
            from IPy import IP
            for ip in ips:
                self.append(IP(ip))
        except ImportError:
            pass

    def __contains__(self, ip):
        try:
            for net in self:
                if ip in net:
                    return True
        except Exception:
            pass
        return False
