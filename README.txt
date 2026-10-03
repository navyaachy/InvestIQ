INVESTIQ PORTFOLIO RISK UPGRADE

1. Extract this folder directly into:
   C:\InvestIQ\InvestIQ

2. Double-click RUN_UPGRADE.bat

3. Wait for:
   Portfolio Risk + Diversification installed successfully.

4. In PowerShell, restart Streamlit:
   cd C:\InvestIQ\InvestIQ
   $env:PYTHONPATH="."
   streamlit run src\investment_guru\ui\app.py

The upgrade automatically backs up your existing app.py before changing it.
No manual code editing is required.
