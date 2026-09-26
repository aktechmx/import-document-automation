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

def extraer_informacion_pdfs(ruta_pdf1, ruta_pdf2):
    '''Extrae la información de los archivos PDF '''
    precio_x_libra = 0.0
    fecha_factura = ""
    
    # DICCIONARIO PARA FORMATEAR LA FECHA
    meses_esp = {1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"}
    
    # ==========================================
    #       LEER PDF 1 (Factura / General)
    # ==========================================
    with pdfplumber.open(ruta_pdf1) as pdf1:
        for page in pdf1.pages:
            tablas_factura = page.extract_tables()
            for tabla in tablas_factura:
                if not tabla or len(tabla) < 2: continue
                df_fac = pd.DataFrame(tabla)
                
                for r_idx in range(len(df_fac)):
                    for c_idx in range(len(df_fac.columns)):
                        celda = str(df_fac.iloc[r_idx, c_idx]).lower()
                        
                        # LOCALIZACIÓN Y FORMATEO DE FECHA (DD-MMM-AAAA)
                        if 'date' in celda and ('shipped' in celda or 'envoi' in celda):
                            if r_idx + 1 < len(df_fac):
                                valor_abajo = str(df_fac.iloc[r_idx + 1, c_idx]).strip()
                                if re.search(r'\d', valor_abajo) and not fecha_factura:
                                    fecha_cruda = valor_abajo.upper()
                                    try:
                                        # CON PANDAS SE REALIZA EL CAMBIO DE FECHA
                                        dt = pd.to_datetime(fecha_cruda)
                                        # NUEVO FORMATO
                                        fecha_factura = f"{dt.day:02d}-{meses_esp[dt.month]}-{dt.year}"
                                    except:
                                        fecha_factura = fecha_cruda # Por si acaso falla, pasamos la original
                                    
                                    
                        # LOCALIZADOR DE PRECIO
                        if 'unit price' in celda or 'unitaire' in celda:
                            for i in range(r_idx + 1, len(df_fac)):
                                valor_abajo = str(df_fac.iloc[i, c_idx]).strip()
                                extraccion = re.search(r'([0-9]+\.[0-9]{2,5})', valor_abajo)
                                if extraccion and precio_x_libra == 0.0:
                                    precio_x_libra = float(extraccion.group(1))
                                    break 
                                    
    if precio_x_libra == 0.0:
        respuesta= solicitar_dato_emergente("Ingresa el precio por libra en dólares")
        precio_x_libra = float(respuesta)
    if not fecha_factura:
        fecha_cruda = solicitar_dato_emergente("Ingresa la fecha manualmente.\nEjemplo: 8/7/2026").upper()
        try:
            dt = pd.to_datetime(fecha_cruda)
            fecha_factura = f"{dt.day:02d}-{meses_esp[dt.month]}-{dt.year}"
        except:
            fecha_factura = fecha_cruda

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
        precio_unit_kg = precio_x_libra * 2.2046
        valor_total = total_libras * precio_x_libra

        # --- EMPAQUETADO FINAL ---
        datos_maestros = {
            "cert_num": cert_num,
            "trip_num": trip_num,
            "varilla_aluminio": varilla_aluminio,
            "diametro": diametro,
            "total_libras": total_libras,
            "precio_x_libra": precio_x_libra,
            "denomi_social": denomi_social,
            "address": address,
            "peso_kg": peso_kg,
            "precio_unit_kg": precio_unit_kg,
            "valor_total": valor_total,
            "fecha": fecha_factura,
            "heats": {} 
        }
        
        for heat, quimicos in quimicos_por_heat.items():
            datos_maestros["heats"][heat] = {
                "quimicos": quimicos,
                "peso_lbs": pesos_por_heat.get(heat, {}).get("lbs", 0.0),
                "peso_kgs": pesos_por_heat.get(heat, {}).get("kgs", 0.0)
            }
            
    return [datos_maestros]