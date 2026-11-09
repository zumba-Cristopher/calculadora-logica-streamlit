import itertools
import re

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Calculadora de Tablas de Verdad", page_icon="🧮", layout="centered")

st.title("🧮 Calculadora de Tablas de Verdad")
st.write(
    "Construye una expresión de lógica proposicional y genera su tabla de verdad. "
    "La tabla utiliza **1 para verdadero** y **0 para falso**."
)

# Constructor visual
if "expresion" not in st.session_state:
    st.session_state.expresion = ""

st.subheader("1. Construye tu expresión")

variables = ["P", "Q", "R", "S"]
cols = st.columns(4)
for i, variable in enumerate(variables):
    with cols[i]:
        if st.button(variable, key=f"var_{variable}", use_container_width=True):
            st.session_state.expresion += variable

st.markdown("**Conectores lógicos**")
conectores = [
    ("∧", "Conjunción"),
    ("∨", "Disyunción"),
    ("¬", "Negación"),
    ("⊕", "Disyunción exclusiva"),
    ("→", "Implicación"),
    ("↔", "Bicondicional"),
    ("(", "Abrir paréntesis"),
    (")", "Cerrar paréntesis"),
]
for start in range(0, len(conectores), 4):
    cols = st.columns(4)
    for j, (simbolo, descripcion) in enumerate(conectores[start:start + 4]):
        with cols[j]:
            if st.button(f"{simbolo}\n{descripcion}", key=f"op_{simbolo}", use_container_width=True):
                if simbolo == "¬":
                    st.session_state.expresion += "¬"
                elif simbolo in ("∧", "∨", "⊕", "→", "↔"):
                    st.session_state.expresion += f" {simbolo} "
                else:
                    st.session_state.expresion += simbolo

col_a, col_b = st.columns(2)
with col_a:
    if st.button("🧹 Limpiar expresión", use_container_width=True):
        st.session_state.expresion = ""
with col_b:
    st.button("ℹ️ Ver ayuda", key="ayuda", use_container_width=True)

st.text_input(
    "Expresión lógica (también puedes escribirla directamente):",
    key="expresion",
    placeholder="Ejemplo: (P ∧ Q) → ¬R",
)

with st.expander("Guía de conectores y ejemplos"):
    st.markdown(
        """
        - **∧ Conjunción:** verdadera solo si ambas proposiciones son verdaderas.
        - **∨ Disyunción:** verdadera si al menos una proposición es verdadera.
        - **¬ Negación:** invierte el valor de verdad.
        - **⊕ Disyunción exclusiva:** verdadera cuando los valores son diferentes.
        - **→ Implicación:** falsa únicamente cuando el antecedente es 1 y el consecuente es 0.
        - **↔ Bicondicional:** verdadera cuando ambos valores son iguales.

        Puedes usar paréntesis para indicar el orden de evaluación. Variables permitidas: P, Q, R y S.
        """
    )

# Analizador de expresiones: respeta la precedencia lógica y no usa eval().
TOKEN_RE = re.compile(r"\s*([PQRS]|[01]|[¬∧∨⊕→↔()]|NOT|AND|OR|XOR)\s*", re.IGNORECASE)

def tokenizar(texto):
    texto = texto.replace("~", "¬").replace("&", "∧").replace("|", "∨")
    texto = texto.replace("!", "¬")
    tokens = []
    pos = 0
    while pos < len(texto):
        if texto[pos:].strip() == "":
            break
        match = TOKEN_RE.match(texto, pos)
        if not match:
            raise ValueError(f"Símbolo no reconocido cerca de: «{texto[pos:pos+8]}»")
        token = match.group(1).upper()
        equivalencias = {"NOT": "¬", "AND": "∧", "OR": "∨", "XOR": "⊕"}
        tokens.append(equivalencias.get(token, token))
        pos = match.end()
    if not tokens:
        raise ValueError("Escribe una expresión lógica.")
    return tokens

class Parser:
    def __init__(self, tokens, valores):
        self.tokens = tokens
        self.valores = valores
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def aceptar(self, token):
        if self.actual() == token:
            self.pos += 1
            return True
        return False

    def analizar(self):
        resultado = self.bicondicional()
        if self.actual() is not None:
            raise ValueError(f"Token inesperado: {self.actual()}")
        return bool(resultado)

    # Precedencia: ¬, ∧, ⊕, ∨, →, ↔
    def bicondicional(self):
        valor = self.implicacion()
        while self.aceptar("↔"):
            derecho = self.implicacion()
            valor = (valor == derecho)
        return valor

    def implicacion(self):
        izquierdo = self.disyuncion()
        if self.aceptar("→"):
            derecho = self.implicacion()
            return (not izquierdo) or derecho
        return izquierdo

    def disyuncion(self):
        valor = self.xor()
        while self.aceptar("∨"):
            derecho = self.xor()
            valor = valor or derecho
        return valor

    def xor(self):
        valor = self.conjuncion()
        while self.aceptar("⊕"):
            derecho = self.conjuncion()
            valor = (valor != derecho)
        return valor

    def conjuncion(self):
        valor = self.unario()
        while self.aceptar("∧"):
            derecho = self.unario()
            valor = valor and derecho
        return valor

    def unario(self):
        if self.aceptar("¬"):
            return not self.unario()
        if self.aceptar("("):
            valor = self.bicondicional()
            if not self.aceptar(")"):
                raise ValueError("Falta cerrar un paréntesis.")
            return valor
        token = self.actual()
        if token in self.valores:
            self.pos += 1
            return bool(self.valores[token])
        if token == "1":
            self.pos += 1
            return True
        if token == "0":
            self.pos += 1
            return False
        if token is None:
            raise ValueError("La expresión está incompleta.")
        raise ValueError(f"Se esperaba una variable o paréntesis, pero apareció: {token}")

def generar_tabla(expresion):
    tokens = tokenizar(expresion)
    variables_usadas = sorted({t for t in tokens if t in {"P", "Q", "R", "S"}})
    if not variables_usadas:
        raise ValueError("Incluye al menos una variable: P, Q, R o S.")

    filas = []
    for combinacion in itertools.product([0, 1], repeat=len(variables_usadas)):
        valores = dict(zip(variables_usadas, combinacion))
        resultado = Parser(tokens, valores).analizar()
        filas.append(list(combinacion) + [int(resultado)])

    return variables_usadas, filas

st.subheader("2. Genera la tabla de verdad")
if st.button("📊 Generar tabla de verdad", type="primary", use_container_width=True):
    try:
        variables_usadas, filas = generar_tabla(st.session_state.expresion)
        tabla = pd.DataFrame(filas, columns=variables_usadas + ["Resultado"])
        st.success(f"Tabla generada correctamente: {len(filas)} combinaciones.")
        st.dataframe(tabla, use_container_width=True, hide_index=True)
        csv = tabla.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Descargar tabla en CSV",
            data=csv,
            file_name="tabla_de_verdad.csv",
            mime="text/csv",
        )
    except ValueError as error:
        st.error(str(error))

st.divider()
st.caption("Estructuras Discretas · Calculadora de lógica proposicional")
