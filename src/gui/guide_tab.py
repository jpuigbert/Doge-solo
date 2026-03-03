from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class GuideTab(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setFont(QFont("Segoe UI", 10))

        guide_html = """
        <h1>🐕 Guia ràpida de DogeSolo</h1>
        <p>Benvingut a DogeSolo, el teu miner en solitari de Dogecoin.</p>

        <h2>📥 1. Instal·lar el node</h2>
        <p>A la pestanya <b>Node</b>, prem <b>Instal·lar node</b>. El programa descarregarà automàticament Dogecoin Core (uns 50 MB).</p>
        <p>Un cop instal·lat, prem <b>Iniciar node</b>. El node començarà a sincronitzar la blockchain (pot trigar hores/dies, necessita ~60 GB).</p>

        <h2>⛏️ 2. Configurar la mineria</h2>
        <p>A la pestanya <b>Mineria</b>, introdueix la teva adreça Dogecoin (comença per 'D').</p>
        <p>Pots triar quants fils de CPU utilitzar (recomanat: tants com nuclis lògics tinguis).</p>
        <p>Prem <b>Començar a minar</b> per iniciar el procés. Veuràs l'hashrate i les estadístiques.</p>

        <h2>💰 3. Gestionar la cartera</h2>
        <p>A la pestanya <b>Cartera</b> pots veure el teu saldo, l'adreça receptora i enviar DOGE.</p>

        <h2>ℹ️ Comissió de desenvolupament (1%)</h2>
        <p>DogeSolo és gratuït, però per mantenir-lo s'aplica una comissió de l'1% sobre cada bloc trobat.</p>
        <p>Està fixada al codi i no es pot modificar.</p>

        """
        self.browser.setHtml(guide_html)

        layout.addWidget(self.browser)