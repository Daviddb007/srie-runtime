# SRIE Runtime

Kernel, SDK, CLI, and loadable modules for the SRIE ecosystem.

## Install

```bash
pip install -e .
```

## Verificación de instalación

Ejecuta estos cuatro comandos para confirmar que SRIE está correctamente instalado:

```bash
# 1. Verifica que pip instaló el paquete
pip list | findstr srie-runtime

# 2. Verifica que el ejecutable existe
where srie

# 3. Verifica la versión del CLI
srie --version

# 4. Verifica que el Runtime puede arrancar
srie doctor
```

**Salida esperada:**

```
srie-runtime v0.1.0

[OK] srie-runtime v0.1.0
[OK] CLI registered
[OK] Kernel package found
[OK] SDK package found
[OK] PyYAML 6.0.3

SRIE Runtime is ready.
```

### Windows PATH Troubleshooting

Si `where srie` no encuentra el ejecutable:

1. **Localiza la carpeta Scripts de Python:**
   ```bash
   py -m site --user-site
   ```
   El ejecutable `srie.exe` estará en el directorio `Scripts` junto a `site-packages`.

2. **Agrega al PATH manualmente:**
   ```bash
   set PATH=%PATH%;C:\Users\TuUsuario\AppData\Local\Programs\Python\Python314\Scripts
   ```
   (Reemplaza la ruta con la que corresponda a tu instalación)

3. **O usa py -m en su lugar:**
   ```bash
   py -m srie.cli.main --version
   ```

4. **Verifica el instalador:**
   ```bash
   py -m pip install -e . --force-reinstall --no-deps
   ```

## Usage

```bash
srie --help
srie doctor
srie init /path/to/project
srie discover /path/to/project
srie indicators /path/to/project
```

## Quick start

```bash
srie init ./mi-proyecto
cd ./mi-proyecto
srie discover .
srie indicators .
srie inspect
```
