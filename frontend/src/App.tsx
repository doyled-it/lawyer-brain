import React, { useState, useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Container from "@mui/material/Container";
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import Box from "@mui/material/Box";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Chatbot from "./components/Chatbot";

const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(false);

  useEffect(() => {
    const savedThemePreference = localStorage.getItem("darkMode");
    if (savedThemePreference) {
      setDarkMode(savedThemePreference === "true");
    }
  }, []);

  const lightTheme = createTheme({
    palette: {
      mode: "light",
    },
  });

  const darkTheme = createTheme({
    palette: {
      mode: "dark",
    },
  });

  const handleThemeChange = () => {
    setDarkMode(!darkMode);
    localStorage.setItem("darkMode", (!darkMode).toString());
  };

  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Box
            component="img"
            src={`${process.env.PUBLIC_URL}/lawyer-brain-good-logo.png`}
            alt="Lawyer Brain Logo"
            sx={{ height: 40, marginRight: 2 }}
          />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Lawyer Brain
          </Typography>
          <FormControlLabel
            control={<Switch checked={darkMode} onChange={handleThemeChange} />}
            label="Dark Mode"
          />
        </Toolbar>
      </AppBar>
      <Container>
        <Chatbot />
      </Container>
    </ThemeProvider>
  );
};

export default App;
