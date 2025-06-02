import pandas as pd
import json
import sys
import io
from datetime import datetime

PROJECT_NAMES = {
    'MER286403207-ADNBRA25': 'ADN Brasil',
    'MER286403208-MER28640': 'ADN Argentina', 
    'MER286403209-ADNCOL25': 'ADN Colombia',
    'MER286403210-ADNMEX25': 'ADN México',
    'MER286403211-ADNURU25': 'ADN Uruguay',
    'MER286403258-CATALAR2': 'Leadership Workshops Argentina',
    'MER286403267-ADNCHI25': 'ADN Chile',
    'MER286403269-CATALUR': 'Leadership Workshops Uruguay',
    'MER286403270-CATALMX': 'Leadership Workshops México',
    'MER286403271-CATALCO': 'Leadership Workshops Colombia',
    'MER286403272-CATALCH': 'Leadership Workshops Chile',
    'MER286403273-CATALBR': 'Leadership Workshops Brasil'
}

def get_month_name(month_num):
    months = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
             7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    return months.get(month_num, "mayo")

def get_first_name(full_name):
    try:
        if ", " in str(full_name):
            return str(full_name).split(", ")[1].split()[0]
        return str(full_name)
    except:
        return str(full_name)

def generate_email(consultant_name, projects_data, month, company_name, include_ids):
    first_name = get_first_name(consultant_name)
    is_english = consultant_name == "De Castro Abreu, Silvia"
    
    if is_english:
        month_en = {"abril": "april", "mayo": "may", "junio": "june"}.get(month, month)
        subject = f"{company_name} - Fees {month_en} 2025 {first_name}"
        email = f"{subject}\n\nHi {first_name}, how are you?\n\nI hope you're doing well. Here are the details for {month_en} 2025 invoicing:\n\n"
        
        total = 0
        currency = ""
        
        for project_code, data in projects_data.items():
            project_name = PROJECT_NAMES.get(project_code, f"({project_code})")
            currency = data['currency']
            amount = data['total_cost']
            ids = ', '.join(data['internal_ids'])
            
            email += f"{project_name.upper()}\n"
            email += f"Project: {project_code}\n"
            
            # Mostrar actividades con rates
            for activity_data in data['activities'].values():
                email += f"- {activity_data['activity']}: {activity_data['hours']} hours @ {activity_data['currency']} {activity_data['rate']}/hour\n"
            
            # Incluir IDs solo si está habilitado
            if include_ids:
                email += f"- IDs: {ids}\n"
            
            email += f"- Subtotal: {currency} {amount:,.2f}\n\n"
            total += amount
        
        email += f"TOTAL TO INVOICE: {currency} {total:,.2f}\n\n"
        email += "Please remember:\n- Upload your invoice to AFN Support form: https://form.jotform.com/243515805505656\n- Include the project codes in your invoice\n\nBest regards!"
        
    else:
        subject = f"{company_name} - Fees {month} 2025 {first_name}"
        email = f"{subject}\n\nHola {first_name}, ¿cómo estás?\n\nTe envío el detalle para la facturación de {month} 2025:\n\n"
        
        total = 0
        currency = ""
        
        for project_code, data in projects_data.items():
            project_name = PROJECT_NAMES.get(project_code, f"({project_code})")
            currency = data['currency']
            amount = data['total_cost']
            ids = ', '.join(data['internal_ids'])
            
            email += f"{project_name.upper()}\n"
            email += f"Proyecto: {project_code}\n"
            
            # Mostrar actividades con rates
            for activity_data in data['activities'].values():
                email += f"- {activity_data['activity']}: {activity_data['hours']} horas @ {activity_data['currency']} {activity_data['rate']}/hora\n"
            
            # Incluir IDs solo si está habilitado
            if include_ids:
                email += f"- IDs: {ids}\n"
            
            email += f"- Subtotal: {currency} {amount:,.2f}\n\n"
            total += amount
        
        email += f"TOTAL A FACTURAR: {currency} {total:,.2f}\n\n"
        email += "Por favor recuerda:\n- Subir tu factura al formulario de AFN Support: https://form.jotform.com/243515805505656\n- Incluir los códigos de proyecto en tu factura\n\nSaludos!"
    
    return subject, email

def process_csv_data(csv_content, config=None):
    """
    Procesa CSV y retorna emails en formato JSON
    
    Args:
        csv_content: String con contenido del CSV
        config: Dict con configuraciones (company_name, include_ids)
    
    Returns:
        Dict con emails generados
    """
    try:
        # Configuración por defecto
        if config is None:
            config = {
                "company_name": "MELI",
                "include_ids": True
            }
        
        # Debug: verificar contenido del CSV
        print(f"DEBUG: CSV content length: {len(csv_content)}")
        lines = csv_content.split('\n')
        print(f"DEBUG: Total lines: {len(lines)}")
        print(f"DEBUG: First line: {lines[0][:100]}...")
        if len(lines) > 1:
            print(f"DEBUG: Second line: {lines[1][:100]}...")
        
        # Leer CSV desde string
        df = pd.read_csv(io.StringIO(csv_content))
        print(f"DEBUG: DataFrame shape: {df.shape}")
        print(f"DEBUG: Columns: {list(df.columns)}")
        
        # Verificar si existe la columna Employee Status
        if 'Employee Status' not in df.columns:
            return {
                "success": False,
                "message": f"Columna 'Employee Status' no encontrada. Columnas disponibles: {list(df.columns)}",
                "emails": []
            }
        
        # Debug: mostrar valores únicos de Employee Status
        employee_statuses = df['Employee Status'].value_counts()
        print(f"DEBUG: Employee Status values: {employee_statuses.to_dict()}")
        
        # Detectar mes automáticamente
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        month_num = df['Date'].dt.month.mode()[0] if not df['Date'].isna().all() else 5
        month = get_month_name(month_num)
        
        # Filtrar solo AFNM
        afnm_data = df[df['Employee Status'] == 'AFNM']
        print(f"DEBUG: AFNM records found: {len(afnm_data)}")
        
        if afnm_data.empty:
            return {
                "success": False,
                "message": f"No se encontraron consultores AFNM. Employee Status values: {employee_statuses.to_dict()}",
                "emails": []
            }
        
        # Limpiar datos
        afnm_data = afnm_data.copy()
        afnm_data['Prj Code'] = afnm_data['Prj Code'].astype(str).str.strip()
        
        # Agrupar por consultor
        consultants = {}
        
        for _, row in afnm_data.iterrows():
            consultant = str(row['Consultant']).strip()
            project = str(row['Prj Code']).strip()
            internal_id = str(row['Internal ID'])
            activity = str(row['Activity']).split(' : ')[-1] if pd.notna(row['Activity']) else 'Activity'
            rate = float(row['Cost (Consultant Curr)']) if pd.notna(row['Cost (Consultant Curr)']) else 0
            hours = float(row['Total Hours']) if pd.notna(row['Total Hours']) else 0
            cost = float(row['Total Cost (Orig Currency)']) if pd.notna(row['Total Cost (Orig Currency)']) else 0
            currency = str(row['Consultant Currency']).strip()
            
            if consultant not in consultants:
                consultants[consultant] = {}
            
            if project not in consultants[consultant]:
                consultants[consultant][project] = {
                    'activities': {},
                    'internal_ids': [],
                    'total_cost': 0,
                    'currency': currency
                }
            
            # Agrupar por actividad y rate
            activity_key = f"{activity}_{rate}"
            if activity_key not in consultants[consultant][project]['activities']:
                consultants[consultant][project]['activities'][activity_key] = {
                    'activity': activity,
                    'rate': rate,
                    'hours': 0,
                    'currency': currency
                }
            
            consultants[consultant][project]['activities'][activity_key]['hours'] += hours
            consultants[consultant][project]['internal_ids'].append(internal_id)
            consultants[consultant][project]['total_cost'] += cost
        
        # Generar emails
        emails = []
        for consultant_name, projects in consultants.items():
            subject, body = generate_email(
                consultant_name, 
                projects, 
                month, 
                config.get('company_name', 'MELI'),
                config.get('include_ids', True)
            )
            
            emails.append({
                "consultant": consultant_name,
                "first_name": get_first_name(consultant_name),
                "subject": subject,
                "body": body,
                "is_english": consultant_name == "De Castro Abreu, Silvia"
            })
        
        return {
            "success": True,
            "message": f"Se generaron {len(emails)} emails para {month}",
            "month": month,
            "total_emails": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error procesando CSV: {str(e)}",
            "emails": []
        }

def main():
    """
    Función principal para uso desde línea de comandos o GitHub Actions
    """
    if len(sys.argv) < 2:
        print("Uso: python email_processor.py <csv_file_path> [config_json]")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    config = {}
    
    # Leer configuración opcional
    if len(sys.argv) > 2:
        try:
            config = json.loads(sys.argv[2])
        except:
            pass
    
    # Leer archivo CSV
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
    except Exception as e:
        result = {
            "success": False,
            "message": f"Error leyendo archivo: {str(e)}",
            "emails": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # Procesar y devolver resultado
    result = process_csv_data(csv_content, config)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
