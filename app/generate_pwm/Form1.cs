using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.IO.Ports;

namespace generate_pwm
{
    public partial class Form1 : Form
    {
        // ── Serial ───────────────────────────────────────────
        private SerialPort _serial = new SerialPort();

        // ── Protocol ─────────────────────────────────────────
        private const byte HEADER_TX = 0xAA;   // PC → STM32
        private const byte HEADER_RX = 0xBB;   // STM32 → PC
        private const int FRAME_RX_LEN = 6;   // BB E1H E1L E2H E2L CRC

        // ── RX state machine ─────────────────────────────────
        private byte[] _rxBuf = new byte[6];
        private int _rxIndex = 0;

        public Form1()
        {
            InitializeComponent();
        }

        // ── Form Load: quét COM ports ─────────────────────────
        private void Form1_Load(object sender, EventArgs e)
        {
            RefreshPorts();
            cmbBaud.SelectedItem = "115200";
            lblVal1.Text = "50 %";
            lblVal2.Text = "50 %";
        }

        private void RefreshPorts()
        {
            cmbPort.Items.Clear();
            cmbPort.Items.AddRange(SerialPort.GetPortNames());
            if (cmbPort.Items.Count > 0) cmbPort.SelectedIndex = 0;
        }

        // ── Refresh button ────────────────────────────────────
        private void btnRefresh_Click(object sender, EventArgs e)
        {
            RefreshPorts();
            Log("Đã cập nhật danh sách cổng COM.");
        }

        // ── Kết nối / Ngắt ───────────────────────────────────
        private void btnConnect_Click(object sender, EventArgs e)
        {
            if (_serial.IsOpen)
            {
                timerAutoSend.Stop();
                chkAutoSend.Checked = false;
                _serial.DataReceived -= Serial_DataReceived;
                _serial.Close();
                btnConnect.Text = "Kết nối";
                btnConnect.BackColor = System.Drawing.Color.LightGreen;
                lblStatus.Text = "Trạng thái: Đã ngắt kết nối";
                lblStatus.ForeColor = System.Drawing.Color.Gray;
                Log("Đã ngắt kết nối.");
                return;
            }

            if (cmbPort.SelectedItem == null)
            {
                MessageBox.Show("Vui lòng chọn cổng COM!", "Lỗi",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                _serial.PortName = cmbPort.SelectedItem.ToString();
                _serial.BaudRate = int.Parse(cmbBaud.SelectedItem?.ToString() ?? "115200");
                _serial.DataBits = 8;
                _serial.Parity = Parity.None;
                _serial.StopBits = StopBits.One;
                _serial.ReadTimeout = 500;
                _serial.WriteTimeout = 500;

                _serial.DataReceived -= Serial_DataReceived;
                _serial.DataReceived += Serial_DataReceived;
                _serial.Open();

                _rxIndex = 0;

                btnConnect.Text = "Ngắt kết nối";
                btnConnect.BackColor = System.Drawing.Color.Salmon;
                lblStatus.Text = $"Trạng thái: Đã kết nối {_serial.PortName} @ {_serial.BaudRate}";
                lblStatus.ForeColor = System.Drawing.Color.DarkGreen;
                Log($"Đã kết nối: {_serial.PortName} @ {_serial.BaudRate} baud");
            }
            catch (Exception ex)
            {
                _serial.DataReceived -= Serial_DataReceived;
                MessageBox.Show($"Lỗi kết nối: {ex.Message}", "Lỗi",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // ── Gửi PWM thủ công ─────────────────────────────────
        private void btnSend_Click(object sender, EventArgs e)
        {
            SendPWM();
        }

        // ── Auto-send toggle ──────────────────────────────────
        private void chkAutoSend_CheckedChanged(object sender, EventArgs e)
        {
            if (chkAutoSend.Checked)
            {
                if (!_serial.IsOpen)
                {
                    MessageBox.Show("Hãy kết nối serial trước!", "Chú ý",
                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    chkAutoSend.Checked = false;
                    return;
                }
                timerAutoSend.Start();
                Log("Auto-send BẬT (50ms).");
            }
            else
            {
                timerAutoSend.Stop();
                Log("Auto-send TẮT.");
            }
        }

        // ── Timer tick → gửi tự động ─────────────────────────
        private void timerAutoSend_Tick(object sender, EventArgs e)
        {
            SendPWM();
        }

        // ── Hàm gửi frame 4 byte ─────────────────────────────
        private void SendPWM()
        {
            if (!_serial.IsOpen)
            {
                Log("⚠ Chưa kết nối serial!");
                return;
            }

            byte pwm1 = (byte)trkPWM1.Value;
            byte pwm2 = (byte)trkPWM2.Value;
            byte crc = (byte)(HEADER_TX ^ pwm1 ^ pwm2);

            byte[] frame = { HEADER_TX, pwm1, pwm2, crc };

            try
            {
                _serial.Write(frame, 0, frame.Length);
                // Chỉ log khi gửi thủ công, tránh spam log khi auto-send
                if (!chkAutoSend.Checked)
                    Log($"→ Gửi: PWM1={pwm1}%, PWM2={pwm2}%");
            }
            catch (Exception ex)
            {
                Log($"⚠ Lỗi gửi: {ex.Message}");
            }
        }

        // ── DataReceived (chạy trên thread serial) ────────────
        private void Serial_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            try
            {
                while (_serial.IsOpen && _serial.BytesToRead > 0)
                {
                    byte b = (byte)_serial.ReadByte();
                    ProcessByte(b);
                }
            }
            catch { /* port đóng giữa chừng */ }
        }

        // ── State machine parse từng byte ────────────────────
        private void ProcessByte(byte b)
        {
            if (_rxIndex == 0)
            {
                if (b == HEADER_RX)
                    _rxBuf[_rxIndex++] = b;
            }
            else
            {
                _rxBuf[_rxIndex++] = b;

                if (_rxIndex >= FRAME_RX_LEN)
                {
                    // Kiểm CRC = XOR bytes 0..4
                    byte crc = 0;
                    for (int i = 0; i < FRAME_RX_LEN - 1; i++)
                        crc ^= _rxBuf[i];

                    if (crc == _rxBuf[FRAME_RX_LEN - 1])
                    {
                        short enc1 = (short)((_rxBuf[1] << 8) | _rxBuf[2]);
                        short enc2 = (short)((_rxBuf[3] << 8) | _rxBuf[4]);

                        // Cập nhật UI từ thread serial → phải Invoke
                        Invoke(new Action(() =>
                        {
                            lblEnc1.Text = $"Encoder 1: {enc1:+#;-#;0} pulse/20ms";
                            lblEnc2.Text = $"Encoder 2: {enc2:+#;-#;0} pulse/20ms";
                            Log($"← Enc1={enc1}, Enc2={enc2}");
                        }));
                    }
                    else
                    {
                        Invoke(new Action(() => Log("⚠ CRC lỗi, bỏ frame.")));
                    }

                    _rxIndex = 0;
                }
            }
        }

        // ── TrackBar cập nhật label ───────────────────────────
        private void trkPWM1_Scroll(object sender, EventArgs e)
            => lblVal1.Text = $"{trkPWM1.Value} %";

        private void trkPWM2_Scroll(object sender, EventArgs e)
            => lblVal2.Text = $"{trkPWM2.Value} %";

        // ── Xoá log ──────────────────────────────────────────
        private void btnClearLog_Click(object sender, EventArgs e)
            => rtbLog.Clear();

        // ── Log helper ───────────────────────────────────────
        private void Log(string msg)
        {
            if (rtbLog.InvokeRequired)
            {
                rtbLog.Invoke(new Action(() => Log(msg)));
                return;
            }
            rtbLog.AppendText($"[{DateTime.Now:HH:mm:ss.fff}] {msg}\n");
            rtbLog.ScrollToCaret();

            // Giới hạn 200 dòng tránh tràn bộ nhớ
            if (rtbLog.Lines.Length > 200)
            {
                rtbLog.Select(0, rtbLog.GetFirstCharIndexFromLine(50));
                rtbLog.SelectedText = "";
            }
        }

        // ── Đóng form → giải phóng serial ────────────────────
        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            timerAutoSend.Stop();
            if (_serial.IsOpen)
            {
                _serial.DataReceived -= Serial_DataReceived;
                _serial.Close();
            }
            _serial.Dispose();
        }

        private void btnClearLog_Click_1(object sender, EventArgs e)
        {

        }
    }
}