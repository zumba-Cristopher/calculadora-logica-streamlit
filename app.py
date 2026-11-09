import streamlit as st
import itertools
import re
import pandas as pd

st.set_page_config(page_title="Calculadora Tabla de la Verdad", layout="centered")
st.title("🧮 Calculadora de Tabla de la Verdad")
st.markdown("Construye tu expresión haciendo clic. El resultado se mostrará exclusivamente en 0 y 1.")

if "expr" not in st.session_state:
    st.session_state.expr = ""

st.subheader("Constructor de Expresión")
variables = ["A", "B", "C", "D", "E", "F"]
cols = st.columns(6)
for i, v in enumerate(variables):
    with cols[i]:
        if st.button(v, key=f"var_{v}", use_container_width=True):
            st.session_state.expr += v

st.markdown("---")
st.subheader("Operadores")
operadores = ["AND", "OR", "NOT", "XOR", "(", ")"]
cols = st.columns(3)
for i, op in enumerate(operadores):
    with cols[i % 3]:
        if st.button(op, key=f"op_{i}", use_container_width=True):
            if op == "NOT":
                st.session_state.expr += " NOT "
            elif op in ("AND", "OR", "XOR"):
                st.session_state.expr += f" {op} "
            else:
                st.session_state.expr += op

col1, col2 = st.columns(2)
with col1:
    if st.button("🧹 Limpiar", use_container_width=True):
        st.session_state.expr = ""
with col2:
    st.code(st.session_state.expr.strip() or "(vacío)", language="text")

def normalizar_expresion(expr):
    e = expr.upper()
    e = re.sub(r"\\bAND\\b", " and ", e)
    e = re.sub(r"\\bOR\\b", " or ", e)
    e = re.sub(r"\\bNOT\\b", " not ", e)
    e = re.sub(r"\\bXOR\\b", " != ", e)
    return e.strip()

def extraer_variables(expr):
    return sorted(set(re.findall(r"\\b[A-F]\\b", expr)))

def generar_tabla(expr):
    expr_normal = normalizar_expresion(expr)
    vars_ = extraer_variables(expr)
    if not vars_:
        raise ValueError("Ingresa una expresión con variables A-F.")
    tabla = []
    for valores in itertools.product([0, 1], repeat=len(vars_)):
        entorno = dict(zip(vars_, valores))
        expresion = expr_normal
        for var, valor in entorno.items():
            expresion = re.sub(rf"\\b{var}\\b", str(bool(valor)), expresion)
        try:
            resultado = eval(expresion, {"__builtins__": {}}, {})
        except Exception:
            raise ValueError("Expresión no válida. Revisa los operadores y paréntesis.")
        tabla.append(list(valores) + [int(bool(resultado))])
    return vars_, tabla

if st.button("📊 Generar Tabla", type="primary", use_container_width=True):
    if not st.session_state.expr.strip():
        st.warning("Ingresa o construye una expresión primero.")
    else:
        try:
            vars_, tabla = generar_tabla(st.session_state.expr)
            df = pd.DataFrame(tabla, columns=vars_ + ["Resultado"])
            st.success(f"Tabla generada para {len(vars_)} variable(s).")
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Descargar CSV", csv, "tabla_verdad.csv", "text/csv")
        except Exception as error:
            st.error(str(error))

st.caption("Estructuras Discretas · Calculadora de tablas de verdad")
