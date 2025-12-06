package com.example.proyectoapp

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.webkit.WebView
import android.webkit.WebViewClient
import android.webkit.WebChromeClient
import android.webkit.ConsoleMessage
import android.widget.ImageButton
import android.widget.Toast
import androidx.activity.addCallback
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.snackbar.Snackbar
import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject
import kotlin.concurrent.thread
import android.util.Log
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse

class MainActivity : AppCompatActivity() {

    // ================= CONFIG =================

    private val BACKEND_URL = "http://98.86.218.95:8000"
    private val INTERVALO_POLLING = 5000L
    private val TAG = "MainActivity"

    private lateinit var webView: WebView
    private lateinit var btnRefresh: ImageButton
    private val handler = Handler(Looper.getMainLooper())
    private var ultimoId: String? = null
    private var pollingActivo = false

    // ================= LIFECYCLE =================

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        Log.d(TAG, "============================================")
        Log.d(TAG, "🚀 INICIANDO APLICACIÓN")
        Log.d(TAG, "============================================")

        initViews()
        setupWebView()

        onBackPressedDispatcher.addCallback(this) {
            if (webView.canGoBack()) webView.goBack()
            else finish()
        }
    }

    override fun onResume() {
        super.onResume()
        Log.d(TAG, "▶️ App resumed - iniciando polling")
        iniciarPolling()
    }

    override fun onPause() {
        super.onPause()
        Log.d(TAG, "⏸️ App paused - deteniendo polling")
        detenerPolling()
    }

    // ================= INIT =================

    private fun initViews() {
        webView = findViewById(R.id.webView)
        btnRefresh = findViewById(R.id.btnRefresh)

        btnRefresh.setOnClickListener {
            Log.d(TAG, "🔄 Botón refresh presionado")
            webView.reload()
            Toast.makeText(this, "Actualizando...", Toast.LENGTH_SHORT).show()
        }
    }

    private fun setupWebView() {
        Log.d(TAG, "⚙️ Configurando WebView...")

        webView.apply {
            // WebViewClient personalizado para debug
            webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    Log.d(TAG, "✅ Página cargada: $url")
                }

                override fun onReceivedError(
                    view: WebView?,
                    errorCode: Int,
                    description: String?,
                    failingUrl: String?
                ) {
                    super.onReceivedError(view, errorCode, description, failingUrl)
                    Log.e(TAG, "❌ Error WebView: $description (código: $errorCode)")
                    Log.e(TAG, "   URL fallida: $failingUrl")
                }

                override fun onReceivedHttpError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    errorResponse: WebResourceResponse?
                ) {
                    super.onReceivedHttpError(view, request, errorResponse)
                    Log.e(TAG, "❌ Error HTTP: ${errorResponse?.statusCode}")
                    Log.e(TAG, "   URL: ${request?.url}")
                }
            }

            // WebChromeClient para ver console.log
            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(msg: ConsoleMessage): Boolean {
                    Log.d("WebView_JS", "[${msg.messageLevel()}] ${msg.message()}")
                    Log.d("WebView_JS", "   Línea ${msg.lineNumber()} de ${msg.sourceId()}")
                    return true
                }
            }

            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                allowContentAccess = true
                allowFileAccess = true
                databaseEnabled = true

                // Configuraciones adicionales para debugging
                mediaPlaybackRequiresUserGesture = false
                javaScriptCanOpenWindowsAutomatically = true
            }

            // AGREGAR EL BRIDGE
            addJavascriptInterface(JSBridge(), "Android")
            Log.d(TAG, "✅ JavaScript Bridge agregado: 'Android'")

            Log.d(TAG, "📡 Cargando URL: $BACKEND_URL")
            loadUrl(BACKEND_URL)
        }
    }

    // ================= POLLING (DESHABILITADO TEMPORALMENTE) =================

    private fun iniciarPolling() {
        Log.d(TAG, "⚠️ Polling deshabilitado temporalmente para debug")
        // Deshabilitado para evitar spam de errores EPERM
        // pollingActivo = true
        // handler.post(pollingRunnable)
    }

    private fun detenerPolling() {
        pollingActivo = false
        handler.removeCallbacks(pollingRunnable)
    }

    private val pollingRunnable = object : Runnable {
        override fun run() {
            if (pollingActivo) {
                verificarNuevoAvistamiento()
                handler.postDelayed(this, INTERVALO_POLLING)
            }
        }
    }

    private fun verificarNuevoAvistamiento() {
        thread {
            try {
                val url = URL("$BACKEND_URL/avistamientos?limite=1")
                val con = url.openConnection() as HttpURLConnection
                con.requestMethod = "GET"
                con.connectTimeout = 5000

                if (con.responseCode == 200) {
                    val json = JSONObject(con.inputStream.bufferedReader().readText())
                    val data = json.getJSONArray("data")

                    if (data.length() > 0) {
                        val ultimo = data.getJSONObject(0)

                        val id = ultimo.getString("id")
                        val especie = ultimo.getString("especie")
                        val accion = ultimo.getString("accion")

                        if (ultimoId != null && id != ultimoId) {
                            mostrarNotificacion(especie, accion)
                        }
                        ultimoId = id
                    }
                }
                con.disconnect()
            } catch (e: Exception) {
                // Silenciar errores de polling
            }
        }
    }

    private fun mostrarNotificacion(especie: String, accion: String) {
        runOnUiThread {
            webView.reload()
            Snackbar.make(
                webView,
                "🦊 $especie: $accion",
                Snackbar.LENGTH_LONG
            ).show()
        }
    }

    // ========== JS BRIDGE ==========

    inner class JSBridge {

        @android.webkit.JavascriptInterface
        fun mostrarDetalles(id: String) {
            Log.d(TAG, "============================================")
            Log.d(TAG, "🎯 JSBridge LLAMADO!")
            Log.d(TAG, "   ID recibido: $id")
            Log.d(TAG, "============================================")

            runOnUiThread {
                Toast.makeText(
                    this@MainActivity,
                    "Cargando detalles...",
                    Toast.LENGTH_SHORT
                ).show()
            }

            obtenerYAbrirDetalles(id)
        }

        @android.webkit.JavascriptInterface
        fun testBridge(mensaje: String) {
            Log.d(TAG, "🧪 Test Bridge recibido: $mensaje")
            runOnUiThread {
                Toast.makeText(
                    this@MainActivity,
                    "Bridge funciona: $mensaje",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    // ========== OBTENER DETALLES Y ABRIR ACTIVITY ==========

    private fun obtenerYAbrirDetalles(id: String) {
        thread {
            try {
                Log.d(TAG, "📡 Consultando: $BACKEND_URL/avistamientos/$id")

                val url = URL("$BACKEND_URL/avistamientos/$id")
                val con = url.openConnection() as HttpURLConnection
                con.requestMethod = "GET"
                con.connectTimeout = 10000
                con.readTimeout = 10000

                val responseCode = con.responseCode
                Log.d(TAG, "📊 Response code: $responseCode")

                if (responseCode == 200) {
                    val responseText = con.inputStream.bufferedReader().readText()
                    Log.d(TAG, "📦 Response OK")

                    val json = JSONObject(responseText)
                    val data = json.getJSONObject("data")

                    val especie = data.optString("especie", "Desconocido")
                    val accion = data.optString("accion", "N/A")
                    val confianza = data.optDouble("confianza", 0.0)
                    val timestamp = data.optString("timestamp", "N/A")
                    val dispositivo = data.optString("dispositivo_id", "N/A")

                    Log.d(TAG, "✅ Datos: $especie - $accion")

                    runOnUiThread {
                        abrirDetalleActivity(especie, accion, confianza, timestamp, dispositivo)
                    }
                } else {
                    Log.e(TAG, "❌ Error HTTP: $responseCode")

                    runOnUiThread {
                        Toast.makeText(
                            this@MainActivity,
                            "Error al cargar detalles",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }
                con.disconnect()

            } catch (e: Exception) {
                Log.e(TAG, "❌ Excepción: ${e.message}", e)

                runOnUiThread {
                    Toast.makeText(
                        this@MainActivity,
                        "Error: ${e.message}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }
    }

    // ========== ABRIR DETALLE ACTIVITY ==========

    private fun abrirDetalleActivity(
        especie: String,
        accion: String,
        confianza: Double,
        timestamp: String,
        dispositivo: String
    ) {
        Log.d(TAG, "🚀 Abriendo DetalleActivity")

        val intent = Intent(this, DetalleActivity::class.java).apply {
            putExtra("especie", especie)
            putExtra("accion", accion)
            putExtra("confianza", confianza)
            putExtra("timestamp", timestamp)
            putExtra("dispositivo", dispositivo)
        }

        startActivity(intent)
    }
}