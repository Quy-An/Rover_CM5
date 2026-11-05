namespace generate_pwm
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.components = new System.ComponentModel.Container();
            this.cmbPort = new System.Windows.Forms.ComboBox();
            this.cmbBaud = new System.Windows.Forms.ComboBox();
            this.btnConnect = new System.Windows.Forms.Button();
            this.btnRefresh = new System.Windows.Forms.Button();
            this.lblStatus = new System.Windows.Forms.Label();
            this.lblPWM1 = new System.Windows.Forms.Label();
            this.trkPWM1 = new System.Windows.Forms.TrackBar();
            this.lblVal1 = new System.Windows.Forms.Label();
            this.lblPWM2 = new System.Windows.Forms.Label();
            this.trkPWM2 = new System.Windows.Forms.TrackBar();
            this.lblVal2 = new System.Windows.Forms.Label();
            this.chkAutoSend = new System.Windows.Forms.CheckBox();
            this.btnSend = new System.Windows.Forms.Button();
            this.lblEnc1 = new System.Windows.Forms.Label();
            this.lblEnc2 = new System.Windows.Forms.Label();
            this.rtbLog = new System.Windows.Forms.RichTextBox();
            this.btnClearLog = new System.Windows.Forms.Button();
            this.timerAutoSend = new System.Windows.Forms.Timer(this.components);
            ((System.ComponentModel.ISupportInitialize)(this.trkPWM1)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.trkPWM2)).BeginInit();
            this.SuspendLayout();
            // 
            // cmbPort
            // 
            this.cmbPort.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbPort.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.cmbPort.FormattingEnabled = true;
            this.cmbPort.Location = new System.Drawing.Point(30, 30);
            this.cmbPort.Name = "cmbPort";
            this.cmbPort.Size = new System.Drawing.Size(140, 36);
            this.cmbPort.TabIndex = 0;
            // 
            // cmbBaud
            // 
            this.cmbBaud.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbBaud.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.cmbBaud.FormattingEnabled = true;
            this.cmbBaud.Items.AddRange(new object[] {
            "9600",
            "57600",
            "115200"});
            this.cmbBaud.Location = new System.Drawing.Point(185, 30);
            this.cmbBaud.Name = "cmbBaud";
            this.cmbBaud.Size = new System.Drawing.Size(140, 36);
            this.cmbBaud.TabIndex = 1;
            // 
            // btnConnect
            // 
            this.btnConnect.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(46)))), ((int)(((byte)(204)))), ((int)(((byte)(113)))));
            this.btnConnect.FlatAppearance.BorderSize = 0;
            this.btnConnect.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnConnect.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnConnect.ForeColor = System.Drawing.Color.White;
            this.btnConnect.Location = new System.Drawing.Point(455, 27);
            this.btnConnect.Name = "btnConnect";
            this.btnConnect.Size = new System.Drawing.Size(120, 34);
            this.btnConnect.TabIndex = 2;
            this.btnConnect.Text = "Kết nối";
            this.btnConnect.UseVisualStyleBackColor = false;
            this.btnConnect.Click += new System.EventHandler(this.btnConnect_Click);
            // 
            // btnRefresh
            // 
            this.btnRefresh.BackColor = System.Drawing.Color.White;
            this.btnRefresh.FlatAppearance.BorderColor = System.Drawing.Color.FromArgb(((int)(((byte)(200)))), ((int)(((byte)(214)))), ((int)(((byte)(229)))));
            this.btnRefresh.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnRefresh.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnRefresh.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(44)))), ((int)(((byte)(62)))), ((int)(((byte)(80)))));
            this.btnRefresh.Location = new System.Drawing.Point(340, 27);
            this.btnRefresh.Name = "btnRefresh";
            this.btnRefresh.Size = new System.Drawing.Size(100, 34);
            this.btnRefresh.TabIndex = 3;
            this.btnRefresh.Text = "↻ Làm mới";
            this.btnRefresh.UseVisualStyleBackColor = false;
            this.btnRefresh.Click += new System.EventHandler(this.btnRefresh_Click);
            // 
            // lblStatus
            // 
            this.lblStatus.AutoSize = true;
            this.lblStatus.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblStatus.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(127)))), ((int)(((byte)(140)))), ((int)(((byte)(141)))));
            this.lblStatus.Location = new System.Drawing.Point(590, 34);
            this.lblStatus.Name = "lblStatus";
            this.lblStatus.Size = new System.Drawing.Size(217, 28);
            this.lblStatus.TabIndex = 4;
            this.lblStatus.Text = "Trạng thái: Chưa kết nối";
            // 
            // lblPWM1
            // 
            this.lblPWM1.AutoSize = true;
            this.lblPWM1.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblPWM1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(44)))), ((int)(((byte)(62)))), ((int)(((byte)(80)))));
            this.lblPWM1.Location = new System.Drawing.Point(30, 105);
            this.lblPWM1.Name = "lblPWM1";
            this.lblPWM1.Size = new System.Drawing.Size(94, 28);
            this.lblPWM1.TabIndex = 5;
            this.lblPWM1.Text = "Motor 1:";
            // 
            // trkPWM1
            // 
            this.trkPWM1.Location = new System.Drawing.Point(120, 95);
            this.trkPWM1.Maximum = 100;
            this.trkPWM1.Name = "trkPWM1";
            this.trkPWM1.Size = new System.Drawing.Size(560, 69);
            this.trkPWM1.TabIndex = 6;
            this.trkPWM1.TickFrequency = 10;
            this.trkPWM1.Value = 50;
            this.trkPWM1.Scroll += new System.EventHandler(this.trkPWM1_Scroll);
            // 
            // lblVal1
            // 
            this.lblVal1.AutoSize = true;
            this.lblVal1.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblVal1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(41)))), ((int)(((byte)(128)))), ((int)(((byte)(185)))));
            this.lblVal1.Location = new System.Drawing.Point(695, 105);
            this.lblVal1.Name = "lblVal1";
            this.lblVal1.Size = new System.Drawing.Size(59, 28);
            this.lblVal1.TabIndex = 7;
            this.lblVal1.Text = "50 %";
            // 
            // lblPWM2
            // 
            this.lblPWM2.AutoSize = true;
            this.lblPWM2.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblPWM2.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(44)))), ((int)(((byte)(62)))), ((int)(((byte)(80)))));
            this.lblPWM2.Location = new System.Drawing.Point(30, 165);
            this.lblPWM2.Name = "lblPWM2";
            this.lblPWM2.Size = new System.Drawing.Size(94, 28);
            this.lblPWM2.TabIndex = 8;
            this.lblPWM2.Text = "Motor 2:";
            // 
            // trkPWM2
            // 
            this.trkPWM2.Location = new System.Drawing.Point(120, 155);
            this.trkPWM2.Maximum = 100;
            this.trkPWM2.Name = "trkPWM2";
            this.trkPWM2.Size = new System.Drawing.Size(560, 69);
            this.trkPWM2.TabIndex = 9;
            this.trkPWM2.TickFrequency = 10;
            this.trkPWM2.Value = 50;
            this.trkPWM2.Scroll += new System.EventHandler(this.trkPWM2_Scroll);
            // 
            // lblVal2
            // 
            this.lblVal2.AutoSize = true;
            this.lblVal2.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblVal2.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(41)))), ((int)(((byte)(128)))), ((int)(((byte)(185)))));
            this.lblVal2.Location = new System.Drawing.Point(695, 165);
            this.lblVal2.Name = "lblVal2";
            this.lblVal2.Size = new System.Drawing.Size(59, 28);
            this.lblVal2.TabIndex = 10;
            this.lblVal2.Text = "50 %";
            // 
            // chkAutoSend
            // 
            this.chkAutoSend.AutoSize = true;
            this.chkAutoSend.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.chkAutoSend.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(44)))), ((int)(((byte)(62)))), ((int)(((byte)(80)))));
            this.chkAutoSend.Location = new System.Drawing.Point(130, 215);
            this.chkAutoSend.Name = "chkAutoSend";
            this.chkAutoSend.Size = new System.Drawing.Size(210, 32);
            this.chkAutoSend.TabIndex = 11;
            this.chkAutoSend.Text = "Tự động gửi (50ms)";
            this.chkAutoSend.UseVisualStyleBackColor = true;
            this.chkAutoSend.CheckedChanged += new System.EventHandler(this.chkAutoSend_CheckedChanged);
            // 
            // btnSend
            // 
            this.btnSend.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(52)))), ((int)(((byte)(152)))), ((int)(((byte)(219)))));
            this.btnSend.FlatAppearance.BorderSize = 0;
            this.btnSend.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSend.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnSend.ForeColor = System.Drawing.Color.White;
            this.btnSend.Location = new System.Drawing.Point(550, 210);
            this.btnSend.Name = "btnSend";
            this.btnSend.Size = new System.Drawing.Size(130, 34);
            this.btnSend.TabIndex = 12;
            this.btnSend.Text = "Gửi PWM →";
            this.btnSend.UseVisualStyleBackColor = false;
            this.btnSend.Click += new System.EventHandler(this.btnSend_Click);
            // 
            // lblEnc1
            // 
            this.lblEnc1.AutoSize = true;
            this.lblEnc1.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblEnc1.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(41)))), ((int)(((byte)(128)))), ((int)(((byte)(185)))));
            this.lblEnc1.Location = new System.Drawing.Point(30, 270);
            this.lblEnc1.Name = "lblEnc1";
            this.lblEnc1.Size = new System.Drawing.Size(195, 38);
            this.lblEnc1.TabIndex = 13;
            this.lblEnc1.Text = "Encoder 1: ---";
            // 
            // lblEnc2
            // 
            this.lblEnc2.AutoSize = true;
            this.lblEnc2.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.lblEnc2.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(41)))), ((int)(((byte)(128)))), ((int)(((byte)(185)))));
            this.lblEnc2.Location = new System.Drawing.Point(420, 270);
            this.lblEnc2.Name = "lblEnc2";
            this.lblEnc2.Size = new System.Drawing.Size(195, 38);
            this.lblEnc2.TabIndex = 14;
            this.lblEnc2.Text = "Encoder 2: ---";
            // 
            // rtbLog
            // 
            this.rtbLog.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(33)))), ((int)(((byte)(37)))), ((int)(((byte)(41)))));
            this.rtbLog.BorderStyle = System.Windows.Forms.BorderStyle.None;
            this.rtbLog.Font = new System.Drawing.Font("Consolas", 9.5F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.rtbLog.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(248)))), ((int)(((byte)(249)))), ((int)(((byte)(250)))));
            this.rtbLog.Location = new System.Drawing.Point(30, 330);
            this.rtbLog.Name = "rtbLog";
            this.rtbLog.ReadOnly = true;
            this.rtbLog.Size = new System.Drawing.Size(790, 140);
            this.rtbLog.TabIndex = 15;
            this.rtbLog.Text = "";
            // 
            // btnClearLog
            // 
            this.btnClearLog.BackColor = System.Drawing.Color.White;
            this.btnClearLog.FlatAppearance.BorderColor = System.Drawing.Color.FromArgb(((int)(((byte)(200)))), ((int)(((byte)(214)))), ((int)(((byte)(229)))));
            this.btnClearLog.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnClearLog.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.btnClearLog.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(127)))), ((int)(((byte)(140)))), ((int)(((byte)(141)))));
            this.btnClearLog.Location = new System.Drawing.Point(30, 485);
            this.btnClearLog.Name = "btnClearLog";
            this.btnClearLog.Size = new System.Drawing.Size(100, 32);
            this.btnClearLog.TabIndex = 16;
            this.btnClearLog.Text = "Xoá log";
            this.btnClearLog.UseVisualStyleBackColor = false;
            this.btnClearLog.Click += new System.EventHandler(this.btnClearLog_Click_1);
            // 
            // timerAutoSend
            // 
            this.timerAutoSend.Interval = 50;
            this.timerAutoSend.Tick += new System.EventHandler(this.timerAutoSend_Tick);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(9F, 20F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(240)))), ((int)(((byte)(244)))), ((int)(((byte)(248)))));
            this.ClientSize = new System.Drawing.Size(850, 545);
            this.Controls.Add(this.btnClearLog);
            this.Controls.Add(this.rtbLog);
            this.Controls.Add(this.lblEnc2);
            this.Controls.Add(this.lblEnc1);
            this.Controls.Add(this.btnSend);
            this.Controls.Add(this.chkAutoSend);
            this.Controls.Add(this.lblVal2);
            this.Controls.Add(this.trkPWM2);
            this.Controls.Add(this.lblPWM2);
            this.Controls.Add(this.lblVal1);
            this.Controls.Add(this.trkPWM1);
            this.Controls.Add(this.lblPWM1);
            this.Controls.Add(this.lblStatus);
            this.Controls.Add(this.btnRefresh);
            this.Controls.Add(this.btnConnect);
            this.Controls.Add(this.cmbBaud);
            this.Controls.Add(this.cmbPort);
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Motor Controller Dashboard";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.Form1_FormClosing);
            this.Load += new System.EventHandler(this.Form1_Load);
            ((System.ComponentModel.ISupportInitialize)(this.trkPWM1)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.trkPWM2)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.ComboBox cmbPort;
        private System.Windows.Forms.ComboBox cmbBaud;
        private System.Windows.Forms.Button btnConnect;
        private System.Windows.Forms.Button btnRefresh;
        private System.Windows.Forms.Label lblStatus;
        private System.Windows.Forms.Label lblPWM1;
        private System.Windows.Forms.TrackBar trkPWM1;
        private System.Windows.Forms.Label lblVal1;
        private System.Windows.Forms.Label lblPWM2;
        private System.Windows.Forms.TrackBar trkPWM2;
        private System.Windows.Forms.Label lblVal2;
        private System.Windows.Forms.CheckBox chkAutoSend;
        private System.Windows.Forms.Button btnSend;
        private System.Windows.Forms.Label lblEnc1;
        private System.Windows.Forms.Label lblEnc2;
        private System.Windows.Forms.RichTextBox rtbLog;
        private System.Windows.Forms.Button btnClearLog;
        private System.Windows.Forms.Timer timerAutoSend;
    }
}

