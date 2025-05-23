
import streamlit as st
from fpdf import FPDF
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Cortes de Aluminio", layout="centered")
st.title("📐➗ Cortes de Aluminio con PDF")

def mostrar_y_guardar_grafico(barra, retazo_mm, largo_barra_mm, index, cod):
    fig, ax = plt.subplots(figsize=(10, 0.6))
    start = 0
    for medida in barra:
        ax.barh(0, medida, left=start, height=0.25, color='#B0B0B0', edgecolor='black')
        ax.text(start + medida / 2, 0, f"{int(medida)}", ha='center', va='center', fontsize=7)
        start += medida
    if retazo_mm > 0:
        color = '#78C000' if retazo_mm >= 1000 else '#D62728'
        ax.barh(0, retazo_mm, left=start, height=0.25, color=color, edgecolor='black')
        ax.text(start + retazo_mm / 2, 0, f"{int(retazo_mm)}", ha='center', va='center', fontsize=7)
    ax.set_xlim(0, largo_barra_mm)
    ax.set_yticks([])
    ax.set_xlabel("mm")
    st.pyplot(fig)
    img_path = f"barra_{cod}_{index}.png"
    fig.savefig(img_path, bbox_inches='tight')
    plt.close(fig)
    return img_path

if "perfiles" not in st.session_state:
    st.session_state.perfiles = []

if "finalizado" not in st.session_state:
    st.session_state.finalizado = False

if not st.session_state.finalizado:
    with st.form("perfil_form"):
        st.subheader("Ingresar datos de un perfil")
        codigo = st.text_input("Código del perfil")
        peso_metro = st.number_input("Peso del perfil (kg/m)", min_value=0.0, step=0.01)
        largo_barra_m = st.number_input("Largo de barra (máx. 6.20 m)", min_value=0.0, step=0.01)
        largo_barra_mm = largo_barra_m * 1000
        if largo_barra_m > 6.20:
            st.error("⚠️ SUPERA LARGO DE BARRA")
        precio_kg = st.number_input("Precio del kg de aluminio ($)", min_value=0.0, step=0.01)
        num_cortes = st.number_input("Cantidad de tipos de corte", min_value=1, step=1)

        cortes = []
        for i in range(int(num_cortes)):
            st.markdown(f"**Corte #{i+1}**")
            medida = st.number_input(f"Medida (mm) del corte #{i+1}", min_value=1.0, step=1.0, key=f"medida{i}")
            ajuste = st.radio(f"¿Tiene ajuste en el corte #{i+1}?", ("No", "Sumar", "Restar"), key=f"ajuste{i}")
            if ajuste != "No":
                valor_ajuste = st.number_input("Cantidad a ajustar (mm)", min_value=0.0, step=1.0, key=f"ajuste_valor{i}")
                medida += valor_ajuste if ajuste == "Sumar" else -valor_ajuste
            cantidad = st.number_input(f"Cantidad de cortes de {medida:.1f} mm", min_value=1, step=1, key=f"cant{i}")
            cortes.extend([medida] * int(cantidad))

        otro = st.radio("¿Desea ingresar otro perfil?", ("S", "N"))
        submitted = st.form_submit_button("Agregar perfil")

        if submitted:
            st.session_state.perfiles.append({
                "codigo": codigo,
                "peso_metro": peso_metro,
                "largo_barra_mm": largo_barra_mm,
                "precio_kg": precio_kg,
                "cortes": cortes
            })
            if otro == "N":
                st.session_state.finalizado = True
            st.experimental_rerun()

if st.session_state.finalizado:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 12)
    for perfil in st.session_state.perfiles:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Perfil: {perfil['codigo']}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Peso por metro: {perfil['peso_metro']} kg/m", ln=True)
        pdf.cell(0, 10, f"Precio por kg: ${perfil['precio_kg']}", ln=True)
        pdf.cell(0, 10, f"Largo de barra: {perfil['largo_barra_mm'] / 1000:.2f} m", ln=True)

        cortes = sorted(perfil["cortes"], reverse=True)
        largo_barra_mm = perfil["largo_barra_mm"]
        barras = []
        retazos = []

        todos_cortes = cortes.copy()
        while todos_cortes:
            disponible = largo_barra_mm
            barra = []
            for medida in todos_cortes[:]:
                if medida <= disponible:
                    barra.append(medida)
                    disponible -= medida
                    todos_cortes.remove(medida)
            barras.append(barra)
            retazos.append(disponible)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Cortes útiles:", ln=True)
        pdf.set_font("Arial", '', 11)
        for barra in barras:
            for medida in barra:
                peso = (medida / 1000) * perfil["peso_metro"]
                costo = peso * perfil["precio_kg"]
                pdf.cell(0, 8, f"- {medida:.1f} mm -> {peso:.3f} kg - ${costo:.2f}", ln=True)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Retazos:", ln=True)
        pdf.set_font("Arial", '', 11)
        for ret_mm in retazos:
            peso = (ret_mm / 1000) * perfil["peso_metro"]
            costo = peso * perfil["precio_kg"]
            tipo = "UTILIZABLE" if ret_mm >= 1000 else "SCRAP"
            pdf.cell(0, 8, f"- {ret_mm:.1f} mm -> {peso:.3f} kg - ${costo:.2f} [{tipo}]", ln=True)

        pdf.cell(0, 10, "Gráficos:", ln=True)
        for i, barra in enumerate(barras):
            img_path = mostrar_y_guardar_grafico(barra, retazos[i], largo_barra_mm, i, perfil["codigo"])
            pdf.image(img_path, w=180)
            os.remove(img_path)

        pdf.cell(0, 10, "", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    st.download_button(
        label="📄 Descargar PDF",
        data=pdf_bytes,
        file_name="cortes_aluminio_multi.pdf",
        mime="application/pdf"
    )
    st.button("🔁 Reiniciar", on_click=lambda: st.session_state.clear())
