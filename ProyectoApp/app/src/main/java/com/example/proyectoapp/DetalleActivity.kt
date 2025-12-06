package com.example.proyectoapp

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import java.text.SimpleDateFormat
import java.util.*

class DetalleActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_detalle)

        // Configurar ActionBar si existe
        supportActionBar?.apply {
            setDisplayHomeAsUpEnabled(true)
            title = "Detalles"
        }

        val txtEspecie = findViewById<TextView>(R.id.txtEspecie)
        val txtAccion = findViewById<TextView>(R.id.txtAccion)
        val txtConfianza = findViewById<TextView>(R.id.txtConfianza)
        val txtFecha = findViewById<TextView>(R.id.txtFecha)
        val txtDispositivo = findViewById<TextView>(R.id.txtDispositivo)
        val btnCerrar = findViewById<Button>(R.id.btnCerrar)

        // =========== RECIBIR DATOS DEL INTENT ===========
        val especie = intent.getStringExtra("especie") ?: "Desconocido"
        val accion = intent.getStringExtra("accion") ?: "N/A"
        val confianza = intent.getDoubleExtra("confianza", -1.0)
        val timestamp = intent.getStringExtra("timestamp") ?: "N/A"
        val dispositivo = intent.getStringExtra("dispositivo") ?: "N/A"

        // =========== FORMATEAR Y MOSTRAR DATOS ===========
        txtEspecie.text = "Especie: $especie"
        txtAccion.text = "Acción: $accion"

        txtConfianza.text = if (confianza >= 0) {
            "Confianza: ${(confianza * 100).toInt()}%"
        } else {
            "Confianza: N/A"
        }

        txtFecha.text = "Fecha: ${formatearFecha(timestamp)}"
        txtDispositivo.text = "Dispositivo: $dispositivo"

        // =========== BOTÓN CERRAR ===========
        btnCerrar.setOnClickListener {
            finish()
        }
    }

    // Formatear fecha legible
    private fun formatearFecha(isoString: String): String {
        return try {
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.getDefault())
            inputFormat.timeZone = TimeZone.getTimeZone("UTC")

            val outputFormat = SimpleDateFormat("dd MMM yyyy, HH:mm", Locale("es", "CL"))

            val fecha = inputFormat.parse(isoString)
            fecha?.let { outputFormat.format(it) } ?: isoString
        } catch (e: Exception) {
            isoString
        }
    }

    // Manejar el botón de back del ActionBar
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}