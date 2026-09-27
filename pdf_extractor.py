import pdfplumber
import pandas as pd
import re
import math
import tkinter as tk
from tkinter import simpledialog

def solicitar_dato_emergente(mensaje):
    '''Abre ventana emergente para pedir datos manuales en caso de no encontrar el dato completo'''
    root = tk.Tk()
    root.withdraw()
    respuesta = simpledialog.askstring("Dato no encontrado",mensaje)
    return respuesta if respuesta else "0" # Devuelve 0 si se cancela la ventana.

def extract_invoice_data(invoice_path):
    """Extract the price per pound and shipping date from invoice PDF."""
    price_per_pound = 0.0
    invoice_date = ""

    spanish_months = {
        1: "ENERO",
        2: "FEBRERO",
        3: "MARZO",
        4: "ABRIL",
        5: "MAYO",
        6: "JUNIO",
        7: "JULIO",
        8: "AGOSTO",
        9: "SEPTIEMBRE",
        10: "OCTUBRE",
        11: "NOVIEMBRE",
        12: "DICIEMBRE"
    }
    with pdfplumber.open(invoice_path) as pdf:
        for page in pdf.pages:
            invoice_tables = page.extract_tables()

            for table in invoice_tables:
                if not table or len(table) < 2:
                    continue

                invoice_df = pd.DataFrame(table)

                for row_idx in range(len(invoice_df)):
                    for col_idx in range(len(invoice_df.columns)):
                        cell = str(
                        invoice_df.iloc[row_idx, col_idx]).lower()

                        # FIND AND FORMAT SHIPPING DATE
                        if 'date' in cell and (
                            'shipped' in cell or 'envoi' in cell):
                                if row_idx + 1 < len(invoice_df):
                                    value_below = str(
                                        invoice_df.iloc[
                                            row_idx + 1,
                                            col_idx
                                        ]
                                    ).strip()

                                    if (
                                        re.search(r'\d',value_below)
                                        and not invoice_date
                                    ):
                                        raw_date = value_below.upper()
                                        try:
                                            dt = pd.to_datetime(raw_date)
                                            invoice_date = (
                                                f"{dt.day:02d}-"
                                                f"{spanish_months[dt.month]}-"
                                                f"{dt.year}"
                                            )
                                        except (ValueError, TypeError):
                                            invoice_date = raw_date

                        # FIND UNIT PRICE
                        if 'unit price' in cell or 'unitaire' in cell:
                            for i in range(
                                row_idx + 1,
                                len(invoice_df)
                            ):
                                value_below = str(
                                    invoice_df.iloc[i, col_idx]
                                ).strip()

                                match = re.search(
                                    r'([0-9]+\.[0-9]{2,5})',
                                    value_below
                                )

                                if match and price_per_pound == 0.0:
                                    price_per_pound = float(
                                        match.group(1)
                                    )
                                    break

    if price_per_pound == 0.0:
        response = solicitar_dato_emergente(
            "Enter the price per pound in USD"
        )
        price_per_pound = float(response)

    if not invoice_date:
        raw_date = solicitar_dato_emergente(
            "Enter the date manually.\nExample: 8/7/2026"
        ).upper()

        try:
            dt = pd.to_datetime(raw_date)
            invoice_date = (
                f"{dt.day:02d}-"
                f"{spanish_months[dt.month]}-"
                f"{dt.year}"
            )
        except (ValueError, TypeError):
            invoice_date = raw_date

    return price_per_pound, invoice_date

def extraer_informacion_pdfs(ruta_pdf1, ruta_pdf2):

    price_per_pound, invoice_date = extract_invoice_data(ruta_pdf1)

    # ==========================================
    #    LEER PDF 2 (Certificado / Reporte)
    # ==========================================
    
    cert_num = "No encontrado"
    trip_num = "No encontrado"
    total_libras = 0.0
    
    with pdfplumber.open(ruta_pdf2) as pdf2:
        texto_pdf2 = ""
        for page in pdf2.pages:
            texto_pdf2 += page.extract_text() + "\n"
            
        # --- EXTRACCIÓN DEL TEXTO ---
        busqueda_empresa = re.search(r'(?i)Ship From\s*\n\s*(.*?)\s*\n\s*(.*?Canada|.*?QC.*?CA|.*?QC.*?Canada)', texto_pdf2)
        denomi_social = busqueda_empresa.group(1).strip() if busqueda_empresa else "NO ENCONTRADO"
        address = busqueda_empresa.group(2).replace('\n', ' ').strip() if busqueda_empresa else "NO ENCONTRADA"

        busqueda_varilla = re.search(r'(?i)COILED ALUMINUM\s*ROD\s+((.*?)\s+([0-9\.]+))\s*IN', texto_pdf2)
        
        if busqueda_varilla:
            varilla_aluminio = busqueda_varilla.group(1).strip()  # Atrapa ej. "1350 C94D H12 0.472"
            diametro = busqueda_varilla.group(3).strip()          # Atrapa ej. "0.472"
        else:
            # Fallback en caso de que el texto del PDF cambie drásticamente
            varilla_aluminio = "NO ENCONTRADO"
            diametro = "NO ENCONTRADO"

        # --- 2. EXTRACCIÓN EN TABLAS (BÚSQUEDA MULTI-PÁGINA) ---
        tablas = []
        # Leemos desde la página 2 (índice 1) hasta la última página que tenga el PDF
        for i in range(1, len(pdf2.pages)):
            tablas_extraidas = pdf2.pages[i].extract_tables()
            if tablas_extraidas:
                tablas.extend(tablas_extraidas) # Juntamos todas las tablas en una sola súper-lista
                
        quimicos_por_heat = {}
        pesos_por_heat = {}
        
        for tabla in tablas:
            if not tabla or len(tabla) < 2: continue
            df = pd.DataFrame(tabla)
            
            for r_idx in range(len(df)):
                row_vals = [str(x).strip().upper() for x in df.iloc[r_idx].values]
                
                # Datos del Viaje
                for c_idx, celda in enumerate([x.lower() for x in row_vals]):
                    if 'cert number' in celda and r_idx + 1 < len(df):
                        extr = re.search(r'([A-Z0-9]+-[0-9]+(?:-[0-9]+)?)', str(df.iloc[r_idx+1, c_idx]))
                        if extr and cert_num == "No encontrado": cert_num = extr.group(1)
                    if 'trip number' in celda and r_idx + 1 < len(df):
                        extr = re.search(r'([A-Z0-9]+-[0-9]+)', str(df.iloc[r_idx+1, c_idx]))
                        if extr and trip_num == "No encontrado": trip_num = extr.group(1)
                    if 'quantity shipped' in celda and r_idx + 1 < len(df):
                        m = re.search(r'([0-9,]+\.[0-9]+)', str(df.iloc[r_idx+1, c_idx]))
                        if m and total_libras == 0.0: total_libras = float(m.group(1).replace(',', ''))
                
                # LOCALIZAR LOS PESOS (LB y KG) POR CADA HEAT
                heat_id_peso = next((x for x in row_vals if re.match(r'^R[0-9A-Z]{5,10}$', x)), None)
                if heat_id_peso:
                    nums = []
                    for x in row_vals:
                        cln = x.replace(',', '')
                        if re.match(r'^[0-9]+(\.[0-9]+)?$', cln) and float(cln) > 100: 
                            nums.append(float(cln))
                    if len(nums) >= 2:
                        lbs, kgs = nums[0], nums[-1]
                        if kgs > lbs: lbs, kgs = kgs, lbs
                        if heat_id_peso not in pesos_por_heat:
                            pesos_por_heat[heat_id_peso] = {'lbs': 0.0, 'kgs': 0.0}
                        pesos_por_heat[heat_id_peso]['lbs'] += lbs
                        pesos_por_heat[heat_id_peso]['kgs'] += kgs

            # LOCALIZAR LOS QUÍMICOS (APLICA PARA LAS TABLAS CON EL ENCABEZADO)
            df_header = pd.DataFrame(tabla[1:], columns=tabla[0])
            if not pd.isna(df_header.columns[0]):
                col_0_str = str(df_header.columns[0]).lower()
                if 'heat' in col_0_str or 'date' in col_0_str or 'drop' in col_0_str:
                    for valor in df_header[df_header.columns[0]].unique():
                        if pd.isna(valor) or str(valor).strip() in ['', 'None', 'nan']: continue
                        heat_limpio = str(valor).split('/')[-1].strip() if '/' in str(valor) else str(valor).strip()
                        
                        df_filtro = df_header[df_header[df_header.columns[0]] == valor]
                        if not df_filtro.empty:
                            if heat_limpio not in quimicos_por_heat: quimicos_por_heat[heat_limpio] = {}
                            for col in df_header.columns[1:]:
                                if pd.isna(col) or str(col).strip() in ['', 'None']: continue
                                val_quim = str(df_filtro[col].iloc[0]).strip()
                                if val_quim not in ['None', 'nan', '']:
                                    quimicos_por_heat[heat_limpio][str(col).lower().strip()] = val_quim

        if total_libras == 0.0:
            respuesta = solicitar_dato_emergente("Ingresa el total de libras: ")
            total_libras = float(respuesta)

        # --- CÁLCULOS MATEMÁTICOS ---
        peso_kg = math.trunc(total_libras / 2.2046) 
        precio_unit_kg = price_per_pound * 2.2046
        valor_total = total_libras * price_per_pound

        # --- EMPAQUETADO FINAL ---
        datos_maestros = {
            "cert_num": cert_num,
            "trip_num": trip_num,
            "varilla_aluminio": varilla_aluminio,
            "diametro": diametro,
            "total_libras": total_libras,
            "precio_x_libra": price_per_pound,
            "denomi_social": denomi_social,
            "address": address,
            "peso_kg": peso_kg,
            "precio_unit_kg": precio_unit_kg,
            "valor_total": valor_total,
            "fecha": invoice_date,
            "heats": {} 
        }
        
        for heat, quimicos in quimicos_por_heat.items():
            datos_maestros["heats"][heat] = {
                "quimicos": quimicos,
                "peso_lbs": pesos_por_heat.get(heat, {}).get("lbs", 0.0),
                "peso_kgs": pesos_por_heat.get(heat, {}).get("kgs", 0.0)
            }
            
    return [datos_maestros]